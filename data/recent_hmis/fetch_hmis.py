#!/usr/bin/env python3
"""Acquire HMIS district-level 'Data ItemWise Monthly' B.Cummulative XLSX files.

Mirrors the official HMIS Standard Reports tree under data/recent_hmis/raw/
and writes data/recent_hmis/raw/_manifest.json.

Mechanism (verified in Plan Mode):
  - Directory listing: GET {BASE}/getFiles?fpath=<base64(path)>
  - File download:     GET {BASE}/downloadfiles?filepath=<url-encoded(server path)>

Usage:
  python3 fetch_hmis.py            # full acquisition (resumable)
  python3 fetch_hmis.py enumerate  # only list targets, print counts, exit
  python3 fetch_hmis.py retry      # retry previously failed files, strictly
                                   #   sequential with long backoff
"""
import base64
import concurrent.futures
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://hmis.mohfw.gov.in"
CATEGORY = ("Standard Reports/5~C2. Data Itemwise Monthly (up to sub district)"
            "/2. All States Across Districts")
YEARS = ["2020-2021", "2021-2022", "2022-2023", "2023-2024",
         "2024-2025", "2025-2026"]
# For these years only the final annual cumulative file (UpTo_Mar) is wanted.
COMPLETE_YEARS = {"2020-2021", "2021-2022", "2022-2023", "2023-2024"}

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_ROOT = os.path.join(HERE, "raw")
MANIFEST = os.path.join(RAW_ROOT, "_manifest.json")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
WORKERS = 4
RETRIES = 3
BACKOFF = [2.0, 4.0, 8.0]
POLITE_DELAY = 0.15
RETRY_DELAY_BETWEEN = 2.0
RETRY_BACKOFF = [10.0, 20.0]
RETRY_GLOBAL_PAUSE = 45.0
RETRY_CONSEQ_FAIL_LIMIT = 4

CUM_RE = re.compile(r"_UpTo_([A-Za-z]+)\.xlsx$", re.I)
SIZE_RE = re.compile(r"([0-9.]+)\s*(KB|MB|GB|B)", re.I)


def log(*args):
    print(*args, flush=True)


def now_iso():
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def b64url_path(path):
    return base64.b64encode(path.encode("utf-8")).decode("ascii")


def http_get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read()


def get_files(path):
    url = (f"{BASE_URL}/getFiles?fpath="
           + urllib.parse.quote(b64url_path(path)))
    st, _hd, body = http_get(url, timeout=60)
    if st != 200:
        return None
    return json.loads(body)


def strip_base(path):
    return path[len("BASEDIR/"):] if path.startswith("BASEDIR/") else path


def parse_size(value):
    if not value:
        return None
    m = SIZE_RE.search(str(value).strip())
    if not m:
        return None
    mult = {"B": 1, "KB": 1e3, "MB": 1e6, "GB": 1e9}.get(m.group(2).upper(), 1)
    return int(round(float(m.group(1)) * mult))


def enumerate_year(fy):
    top = get_files(CATEGORY)
    if not isinstance(top, list):
        return []
    year_folder = None
    for k in top:
        if k.get("name", "").startswith(fy):
            year_folder = strip_base(k.get("path", ""))
            break
    if year_folder is None:
        return []
    cum = None
    node = get_files(year_folder)
    if not isinstance(node, list):
        return []
    for k in node:
        if k.get("name", "").startswith("B.Cummulative"):
            cum = strip_base(k.get("path", ""))
            break
    if cum is None:
        return []
    recs = []
    states = get_files(cum)
    if not isinstance(states, list):
        return []
    for st in states:
        if not st.get("isdirectory"):
            continue
        state = st.get("name", "")
        sdir = strip_base(st.get("path", ""))
        files = get_files(sdir)
        if not isinstance(files, list):
            continue
        for f in files:
            fname = f.get("name", "")
            if not fname.lower().endswith(".xlsx"):
                continue
            m = CUM_RE.search(fname)
            if not m:
                continue
            spath = strip_base(f.get("path", ""))
            recs.append({
                "fiscal_year": fy,
                "state": state,
                "filename": fname,
                "cumulative_month": m.group(1),
                "server_path": spath,
                "server_file_size": f.get("fileSize"),
                "file_size_bytes": parse_size(f.get("fileSize")),
                "last_modified_date": f.get("lastModifiedDate"),
            })
    return recs


def download_url(server_path):
    filepath = urllib.parse.quote(server_path.replace("&", ":::"), safe="()~.")
    return f"{BASE_URL}/downloadfiles?filepath={filepath}"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(rec):
    fy, state, fname = rec["fiscal_year"], rec["state"], rec["filename"]
    dest_dir = os.path.join(RAW_ROOT, fy, "B.Cummulative", state)
    dest = os.path.join(dest_dir, fname)
    rec["local_path"] = dest

    if os.path.exists(dest):
        rec_hash = rec.get("recorded_sha256")
        if rec_hash:
            try:
                if sha256_file(dest) == rec_hash:
                    rec.update(status="skipped", sha256=rec_hash,
                               http_status=200,
                               error=None, action_time=now_iso())
                    return rec
            except OSError:
                pass
        else:
            # On disk but not in a previous manifest: treat as new acquisition.
            pass

    os.makedirs(dest_dir, exist_ok=True)
    url = download_url(rec["server_path"])
    last_err = None
    for attempt in range(RETRIES):
        try:
            st, hd, body = http_get(url)
            if st == 200 and body:
                with open(dest, "wb") as fh:
                    fh.write(body)
                rec.update(status="downloaded", http_status=st,
                           sha256=sha256_file(dest),
                           error=None, action_time=now_iso())
                time.sleep(POLITE_DELAY)
                return rec
            last_err = f"HTTP {st}"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
        if attempt < RETRIES - 1:
            time.sleep(BACKOFF[attempt])
    rec.update(status="failed", http_status=None,
               sha256=None, error=last_err, action_time=now_iso())
    return rec


def load_previous_hashes():
    prev = {}
    if not os.path.exists(MANIFEST):
        return prev
    try:
        with open(MANIFEST, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return prev
    for r in data:
        if r.get("sha256") and r.get("status") != "failed" and r.get("local_path"):
            prev[r["local_path"]] = r["sha256"]
    return prev


def build_targets():
    all_recs = []
    for fy in YEARS:
        recs = enumerate_year(fy)
        if fy in COMPLETE_YEARS:
            recs = [r for r in recs if r["cumulative_month"].lower() == "mar"]
        all_recs.extend(recs)
    return all_recs


def summarize(results):
    total_bytes = 0
    n_down = n_skip = n_fail = 0
    for r in results:
        if r["status"] == "downloaded":
            n_down += 1
            total_bytes += r.get("file_size_bytes") or 0
        elif r["status"] == "skipped":
            n_skip += 1
            total_bytes += r.get("file_size_bytes") or 0
        else:
            n_fail += 1
    log(f"files enumerated : {len(results)}")
    log(f"downloaded       : {n_down}")
    log(f"skipped (matched): {n_skip}")
    log(f"failed           : {n_fail}")
    log(f"total bytes      : {total_bytes}")
    for r in results:
        if r["status"] == "failed":
            log(f"FAIL {r['fiscal_year']} | {r['state']} | {r['filename']} | {r.get('error')}")


def fetch_retry(rec, delay_between=RETRY_DELAY_BETWEEN):
    """Sequential fetch for previously failed files.
    Returns (rec, consecutive_ok). consecutive_ok Truthy on success so caller
    can detect a global block via repeated failures."""
    fy, state, fname = rec["fiscal_year"], rec["state"], rec["filename"]
    dest_dir = os.path.join(RAW_ROOT, fy, "B.Cummulative", state)
    dest = os.path.join(dest_dir, fname)
    rec["local_path"] = dest
    if os.path.exists(dest) and rec.get("recorded_sha256"):
        try:
            if sha256_file(dest) == rec["recorded_sha256"]:
                rec.update(status="skipped", sha256=rec["recorded_sha256"],
                           http_status=200, error=None, action_time=now_iso())
                return rec, True
        except OSError:
            pass
    os.makedirs(dest_dir, exist_ok=True)
    url = download_url(rec["server_path"])
    for wait in [0.0] + RETRY_BACKOFF:
        if wait:
            time.sleep(wait)
        try:
            st, _hd, body = http_get(url, timeout=90)
            if st == 200 and body:
                with open(dest, "wb") as fh:
                    fh.write(body)
                rec.update(status="downloaded", http_status=st,
                           sha256=sha256_file(dest), error=None,
                           action_time=now_iso())
                time.sleep(delay_between)
                return rec, True
            last_err = f"HTTP {st}"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
    rec.update(status="failed", http_status=None, sha256=None,
               error=last_err, action_time=now_iso())
    return rec, False


def _rec_to_manifest(r):
    return {
        "source_url": download_url(r["server_path"]),
        "server_path": r["server_path"],
        "filename": r["filename"],
        "fiscal_year": r["fiscal_year"],
        "state": r["state"],
        "cumulative_month": r["cumulative_month"],
        "file_size": r.get("server_file_size") or r.get("file_size"),
        "file_size_bytes": r.get("file_size_bytes"),
        "last_modified_date": r["last_modified_date"],
        "sha256": r.get("sha256"),
        "http_status": r.get("http_status"),
        "download_timestamp": r.get("action_time"),
        "status": r["status"],
        "local_path": r.get("local_path"),
        "error": r.get("error"),
    }


def run_retry():
    if not os.path.exists(MANIFEST):
        log("No manifest found; nothing to retry.")
        return
    with open(MANIFEST, "r", encoding="utf-8") as fh:
        old = json.load(fh)
    targets = build_targets()
    by_key = {(r["fiscal_year"], r["state"], r["filename"]): r for r in targets}
    todos = []
    for r in old:
        if r.get("status") != "failed":
            continue
        cur = by_key.get((r["fiscal_year"], r["state"], r["filename"]))
        if not cur:
            continue
        cur["recorded_sha256"] = r.get("sha256")
        todos.append(cur)
    log(f"Retrying {len(todos)} previously failed files (sequential).")
    redo = [_rec_to_manifest(r) for r in old if r.get("status") != "failed"]
    # redo keyed for updates
    redo_by_key = {
        (r["fiscal_year"], r["state"], r["filename"]): r for r in redo
    }
    consecutive_fail = 0
    for rec in todos:
        res, ok = fetch_retry(rec)
        redo_by_key[(res["fiscal_year"], res["state"], res["filename"])] = \
            _rec_to_manifest(res)
        # incremental write so a killed run keeps progress
        merged = sorted(redo_by_key.values(),
                        key=lambda r: (r["fiscal_year"], r["state"],
                                       r["filename"]))
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, indent=2)
        consecutive_fail = 0 if ok else consecutive_fail + 1
        log("  -> %s/%s | %s/%s | %s" % (
            res["fiscal_year"], res["state"], res["filename"],
            res["status"], res.get("error") or ""))
        if not ok and consecutive_fail >= RETRY_CONSEQ_FAIL_LIMIT:
            log(f"Detected global block ({consecutive_fail} consecutive "
                f"failures); pausing {int(RETRY_GLOBAL_PAUSE)}s.")
            time.sleep(RETRY_GLOBAL_PAUSE)
            consecutive_fail = 0
    log(f"Manifest updated: {MANIFEST}")
    summarize(redo_by_key.values())


def run(enumerate_only=False):
    os.makedirs(RAW_ROOT, exist_ok=True)
    prev = {} if enumerate_only else load_previous_hashes()
    targets = build_targets()
    log(f"Enumerated {len(targets)} target files across "
        f"{', '.join(YEARS)}")
    if not targets:
        sys.exit(1)
    if enumerate_only:
        from collections import Counter
        by_fy = Counter(r["fiscal_year"] for r in targets)
        for fy in YEARS:
            log(f"  {fy}: {by_fy.get(fy, 0)} files")
        return

    for r in targets:
        lp = os.path.join(RAW_ROOT, r["fiscal_year"], "B.Cummulative",
                          r["state"], r["filename"])
        r["recorded_sha256"] = prev.get(lp)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch, r): r for r in targets}
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())

    results.sort(key=lambda r: (r["fiscal_year"], r["state"], r["filename"]))

    manifest = []
    for r in results:
        manifest.append({
            "source_url": download_url(r["server_path"]),
            "server_path": r["server_path"],
            "filename": r["filename"],
            "fiscal_year": r["fiscal_year"],
            "state": r["state"],
            "cumulative_month": r["cumulative_month"],
            "file_size": r["server_file_size"],
            "file_size_bytes": r["file_size_bytes"],
            "last_modified_date": r["last_modified_date"],
            "sha256": r.get("sha256"),
            "http_status": r.get("http_status"),
            "download_timestamp": r.get("action_time"),
            "status": r["status"],
            "local_path": r.get("local_path"),
            "error": r.get("error"),
        })
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    log(f"Manifest written: {MANIFEST}")
    summarize(results)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "enumerate":
        run(enumerate_only=True)
    elif mode == "retry":
        run_retry()
    else:
        run()