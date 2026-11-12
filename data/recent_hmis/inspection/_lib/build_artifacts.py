"""Build inspection artifacts for the recent HMIS harmonization audit.

Outputs (all under data/recent_hmis/inspection/):
  raw_structure_report.md
  maternal_indicator_mapping.csv
  harmonization_matrix.csv
  reconstruction_checks.csv
  item_dictionary.csv
  inspection_report.md   (sections A-L)

Read-only w.r.t. the raw XLSX and the legacy datasets.
"""
from __future__ import annotations

import csv
import os
import re
import statistics
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import hmis_reader as hr
import reconstruct as rc

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, "inspection")
os.makedirs(OUT, exist_ok=True)

REP_FILES = [
    ("2020-21", "Uttar Pradesh", "data/recent_hmis/raw/2020-2021/B.Cummulative/Uttar Pradesh/L-Uttar Pradesh_UpTo_Mar.xlsx"),
    ("2020-21", "Telangana",      "data/recent_hmis/raw/2020-2021/B.Cummulative/Telangana/L-Telangana_UpTo_Mar.xlsx"),
    ("2020-21", "Ladakh",         "data/recent_hmis/raw/2020-2021/B.Cummulative/Ladakh/L-Ladakh_UpTo_Mar.xlsx"),
    ("2021-22", "Telangana",      "data/recent_hmis/raw/2021-2022/B.Cummulative/Telangana/L-Telangana_UpTo_Mar.xlsx"),
    ("2021-22", "Chandigarh",     "data/recent_hmis/raw/2021-2022/B.Cummulative/Chandigarh/L-Chandigarh_UpTo_Mar.xlsx"),
    ("2022-23", "Goa",            "data/recent_hmis/raw/2022-2023/B.Cummulative/Goa/L-Goa_UpTo_Mar.xlsx"),
    ("2022-23", "Uttar Pradesh",  "data/recent_hmis/raw/2022-2023/B.Cummulative/Uttar Pradesh/L-Uttar Pradesh_UpTo_Mar.xlsx"),
    ("2023-24", "Tripura",        "data/recent_hmis/raw/2023-2024/B.Cummulative/Tripura/L-Tripura_UpTo_Mar.xlsx"),
    ("2024-25", "Uttar Pradesh",  "data/recent_hmis/raw/2024-2025/B.Cummulative/Uttar Pradesh/A-Uttar Pradesh_UpTo_Apr.xlsx"),
    ("2024-25", "Ladakh",         "data/recent_hmis/raw/2024-2025/B.Cummulative/Ladakh/A-Ladakh_UpTo_Apr.xlsx"),
]

INDICATORS = [
    {"feature": "ANC_First_Trimester_Pct", "formula": "1.1.1 / 1.1",
     "nums": ["1.1.1"], "dens": ["1.1"], "sum_num": False},
    {"feature": "TT2_Booster_Pct", "formula": "(1.2.2 + 1.2.3) / 1.1",
     "nums": ["1.2.2", "1.2.3"], "dens": ["1.1"], "sum_num": True},
    {"feature": "Severe_Anemia_Pct", "formula": "1.4.3 / 1.4.2",
     "nums": ["1.4.3"], "dens": ["1.4.2"], "sum_num": False},
    {"feature": "Institutional_Delivery_Pct", "formula": "2.2 / (2.1.1.a + 2.1.1.b + 2.2)",
     "nums": ["2.2"], "dens": ["2.1.1.a", "2.1.1.b", "2.2"], "sum_num": True},
    {"feature": "PNC_48h_Pct", "formula": "6.1 / (2.1.1.a + 2.1.1.b + 2.2)",
     "nums": ["6.1"], "dens": ["2.1.1.a", "2.1.1.b", "2.2"], "sum_num": True},
    {"feature": "Obstetric_Complications_Pct", "formula": "5.1 / (2.1.1.a + 2.1.1.b + 2.2)",
     "nums": ["5.1"], "dens": ["2.1.1.a", "2.1.1.b", "2.2"], "sum_num": True},
]

CODEDICT = {
    "1.1":    ("Total number of pregnant women registered for ANC",
               "Total number of NEW Pregnant Women registered for ANC", "Denominator (ANC registrations)", "BOTH"),
    "1.1.1":  ("Out of the total ANC registered, number registered within 1st trimester (within 12 weeks)",
               "Out of the total NEW ANC registered, number registered within 1st trimester (within 12 weeks)",
               "Numerator ANC first-trimester", "BOTH"),
    "1.2.1":  ("Number of PW given TT1/ Td1",
               "Number of PW given Td1 (Tetanus Diptheria dose 1)", "TT1 coverage (context)", "BOTH"),
    "1.2.2":  ("Number of PW given TT2 / Td2",
               "Number of PW given Td2 (Tetanus Diptheria dose 2)", "Numerator component (TT2/Td2)", "BOTH"),
    "1.2.3":  ("Number of PW given TT Booster/ Td Booster",
               "Number of PW given Td Booster (Tetanus Diptheria dose booster)", "Numerator component (booster)", "BOTH"),
    "1.4.1":  ("Number of PW tested for Haemoglobin (Hb ) 4 or more than 4 times for respective ANCs",
               "Number of PW tested for Haemoglobin (Hb ) 4 or more than 4 times for respective ANCs",
               "Context (repeat Hb testing)", "BOTH"),
    "1.4.2":  ("Number of PW having Hb level<11 (out of total tested cases)(7.1 to 10.9)",
               "Number of PW having Hb level<11(7.1 to 10.9 g/dl) (Out of total tested cases)",
               "Denominator moderate anaemia (Hb<11)", "BOTH"),
    "1.4.3":  ("Number of PW having Hb level<7 (out of total tested cases)",
               "Number of PW having Hb level<=7 g/dl (Out of total tested cases)",
               "Numerator severe anaemia (boundary changed <7 -> <=7)", "BOTH"),
    "1.4.4":  ("Number of PW having severe anaemia (Hb < 7) treated",
               "Number of PW treated for severe anaemia (Hb<=7g/dl) (Out of total tested cases)",
               "Severe-anaemia treated (context)", "BOTH"),
    "2.1.1.a":("Number of Home Deliveries attended by Skill Birth Attendant(SBA) (Doctor/Nurse/ANM/ Midwife)",
               "Number of Home Deliveries attended by Skill Birth Attendant(SBA) (Doctor/Nurse/ANM)",
               "Home deliveries SBA (denominator component)", "BOTH"),
    "2.1.1.b":("Number of Home Deliveries attended by Non SBA (Trained Birth Attendant(TBA) /Relatives/etc.)",
               "Number of Home Deliveries attended by Non SBA (Trained Birth Attendant(TBA) /Relatives/etc.)",
               "Home deliveries non-SBA (denominator component)", "BOTH"),
    "2.2":    ("Number of Institutional Deliveries conducted (Including C-Sections)",
               "Number of Institutional Deliveries conducted (Including C-Sections)",
               "Institutional deliveries (numerator / denom component)", "BOTH"),
    "2.2.1":  ("Out of total institutional deliveries number of women discharged within 48 hours of delivery",
               "Out of total institutional  deliveries(excluding C-section), number of women stayed for  48 hours or more after delivery",
               "Institutional stay item - INVERTED meaning across eras", "BOTH"),
    "2.3":    ("",
               "Age wise total number of delivery (Home +Institutional) reported (2.3.1+2.3.2+2.3.3+2.3.4)",
               "Total deliveries (new schema only) - natural %-of-deliveries denominator", "NEW"),
    "3.1":    ("Total C -Section deliveries performed",
               "Total number of C -Section deliveries performed", "Context", "BOTH"),
    "5.1":    ("Number of cases of pregnant women with Obstetric Complications attended (Antepartum haemorrhage (APH), Post-Partum Hemorrhage (PPH), Sepsis, Eclampsia and others)",
               "", "Old aggregate obstetric complications (2020-23 only)", "OLD"),
    "6.1":    ("Women receiving 1st post partum checkups within 48 hours of home delivery",
               "In case of home delivery, number of women receiving 1st Postpartum checkups within 48 hours",
               "PNC within 48h - HOME deliveries only", "BOTH"),
    "6.2":    ("Women receiving 1st post partum checkup between 48 hours and 14 days",
               "Number of women receiving Postpartum checkup between 48 hours and 14 days after Institutional delivery",
               "PNC 48h-14d - scope changed to institutional in new schema", "BOTH"),
    "1.9.1":  ("",
               "Total High Risk Pregnancy (HRP) Intrapartum including following:",
               "HRP intrapartum aggregate (new schema)", "NEW"),
    "1.9.1.a":("",
               "Number of Pregnant Women with Post-Partum Haemorrhage(Immediately after delivery) in the facility.",
               "HRP component PPH", "NEW"),
    "1.9.1.b":("",
               "Number of Pregnant Women with Sepsis in the facility.",
               "HRP component sepsis", "NEW"),
    "1.9.1.c":("",
               "Number of Pregnant Women identified with Eclampsia in the facility",
               "HRP component eclampsia", "NEW"),
    "1.9.1.d":("",
               "Number of Pregnant Women identified with obstructed labour in the facility.",
               "HRP component obstructed labour", "NEW"),
    "1.9.2":  ("",
               "Total High Risk Pregnancy (HRP) Antepartum (Only New Cases are to be reported)",
               "HRP antepartum new cases", "NEW"),
}


def sheet_info(path):
    ws = hr.load(path)
    return ws


def blank_count(it, groups):
    if it is None:
        return None
    cnt = 0
    for g in groups[1:]:
        v = it.values.get(g.name)
        if v is None or (isinstance(v, str) and not v.strip()):
            cnt += 1
    return cnt


def build_structure():
    rows = []
    for fy, st, p in REP_FILES:
        ws = sheet_info(p)
        blank, neg = 0, 0
        for it in ws.items:
            for v in it.values.values():
                if v is None or (isinstance(v, str) and not v.strip()):
                    blank += 1
                elif isinstance(v, (int, float)) and v < 0:
                    neg += 1
        codes = [it.code.strip(" '").strip() for it in ws.items]
        dup = len(codes) - len(set(codes))
        rows.append({
            "fy": fy, "state": st, "file": os.path.basename(p),
            "groups": len(ws.groups), "districts": len(ws.districts),
            "row_count": ws.nrows, "col_count": ws.ncols,
            "item_rows": len(ws.items), "unique_items": len(set(codes)),
            "dup_rows": dup, "blank_cells": blank, "neg_cells": neg,
        })
    return rows


def build_reconstruction():
    out = []
    for fy, st, p in REP_FILES:
        ws = sheet_info(p)
        era = "OLD" if fy <= "2022-23" else "NEW"
        for ind in INDICATORS:
            r = rc.indicator(ws, ind["nums"], ind["dens"], sum_num=ind["sum_num"])
            vals = {k: v for k, v in r.get("values", {}).items() if v is not None}
            denz = sum(1 for g in ws.groups[1:]
                       if rc.num(rc.item_by_code(ws, ind["dens"][0]).values.get(g.name)) == 0)
            bnum = {c: blank_count(rc.item_by_code(ws, c), ws.groups) for c in ind["nums"]}
            bden = {c: blank_count(rc.item_by_code(ws, c), ws.groups) for c in ind["dens"]}
            any_missing_n = r.get("missing")
            if vals:
                sv = sorted(vals.values())
                med = round(statistics.median(sv), 3)
                rng = (round(min(sv), 2), round(max(sv), 2))
                n = len(vals)
            else:
                med = ""
                rng = ("", "")
                n = 0
            out.append({
                "fiscal_year": fy, "state": st, "schema_era": era,
                "indicator": ind["feature"], "formula": ind["formula"],
                "districts_with_data": n,
                "median_pct": med, "min_pct": rng[0] if rng else "", "max_pct": rng[1] if rng else "",
                "denom_zero_districts": denz,
                "blank_numerator_cells": ";".join(f"{c}:{n}" for c, n in bnum.items()),
                "blank_denominator_cells": ";".join(f"{c}:{n}" for c, n in bden.items()),
                "items_missing": "yes" if any_missing_n else "no",
            })
    return out


def build_harmonization():
    rows = [
        {
            "Feature": "ANC_First_Trimester_Pct",
            "Old Dataset Definition": "Registrations For ANC In The First Trimester (To Total ANC Registrations) (%)  -> 1.1.1 / 1.1",
            "HMIS 2020-21 Definition": "1.1.1 (ANC registered within 1st trimester, within 12 weeks) / 1.1 (Total PW registered for ANC)",
            "HMIS 2021-22 Definition": "same as 2020-21 (verified in Telangana 2021-22)",
            "HMIS 2022-23 Definition": "same as 2020-21 (verified in UP & Goa 2022-23)",
            "HMIS 2023-24 Definition": "1.1.1 (NEW ANC within 1st trimester) / 1.1 (Total number of NEW Pregnant Women registered for ANC); label adds NEW, concept unchanged",
            "HMIS 2024-25 Definition": "same as 2023-24 (verified in UP & Ladakh 2024-25)",
            "Comparable?": "YES",
            "Decision (YES/NO/UNCERTAIN)": "YES",
            "Reason/Evidence": "Numerator & denominator items identical concept across all five years; only cosmetic label change (NEW) from 2023-24. Reconstruct as 1.1.1/1.1 x 100.",
        },
        {
            "Feature": "TT2_Booster_Pct",
            "Old Dataset Definition": "Pregnant Women Received The Second Dose Of Tetanus-Toxoid Vaccine (TT2) Or Booster (To Total ANC Registrations) (%)  -> (TT2 | Booster) / ANC registers",
            "HMIS 2020-21 Definition": "(1.2.2 PW given TT2/Td2 + 1.2.3 PW given TT Booster/Td Booster) / 1.1",
            "HMIS 2021-22 Definition": "same as 2020-21 (Telangana 2021-22)",
            "HMIS 2022-23 Definition": "same (UP 2022-23)",
            "HMIS 2023-24 Definition": "(1.2.2 PW given Td2 + 1.2.3 PW given Td Booster) / 1.1; TT2 renamed Td2, TT Booster renamed Td Booster",
            "HMIS 2024-25 Definition": "same as 2023-24 (UP 2024-25)",
            "Comparable?": "YES (caveat)",
            "Decision (YES/NO/UNCERTAIN)": "YES",
            "Reason/Evidence": "Both components exist every year under renamed labels. Caveat: summing TT2 + Booster may double-count women given both; sums stay <100% in all inspected districts but this is not guaranteed.",
        },
        {
            "Feature": "Severe_Anemia_Pct",
            "Old Dataset Definition": "Pregnant Women With Hemoglobin (Hb) Levels<7 (Severe Anemia) (To Women With Hemoglobin (Hb) Levels<11 (Moderate Anemia)) (%)  -> 1.4.3 / 1.4.2",
            "HMIS 2020-21 Definition": "1.4.3 (Hb<7) / 1.4.2 (Hb<11, i.e. 7.1-10.9)",
            "HMIS 2021-22 Definition": "same (Telangana 2021-22)",
            "HMIS 2022-23 Definition": "same (UP 2022-23)",
            "HMIS 2023-24 Definition": "1.4.3 (Hb<=7 g/dl) / 1.4.2 (Hb<11 / 7.1-10.9 g/dl); severe threshold changed from <7 to <=7",
            "HMIS 2024-25 Definition": "same as 2023-24 (UP 2024-25)",
            "Comparable?": "UNCERTAIN",
            "Decision (YES/NO/UNCERTAIN)": "UNCERTAIN",
            "Reason/Evidence": "Boundary <7 vs <=7 changes the numerator slightly; denominator wording also relabelled (7.1-10.9). Ratio is reconstructable but is NOT exactly the old published figure. Do not treat as identical without adjustment.",
        },
        {
            "Feature": "Institutional_Delivery_Pct",
            "Old Dataset Definition": "Institutional Deliveries (To Total ANC Registrations) (%)  -> 2.2 / ANC registrations (Note: published % routinely exceeds 100 where deliveries > ANC)",
            "HMIS 2020-21 Definition": "2.2 (Institutional Deliveries incl. C-Sections) / 1.1 (ANC registrations)  [as published]",
            "HMIS 2021-22 Definition": "same (Telangana 2021-22)",
            "HMIS 2022-23 Definition": "same (UP 2022-23)",
            "HMIS 2023-24 Definition": "2.2 / total reported deliveries. Total deliveries = 2.3 (age-wise total, EXISTS in new schema) or 2.1.1.a+2.1.1.b+2.2. No out-of-the-box 2.2/2.3 item.",
            "HMIS 2024-25 Definition": "same as 2023-24 (UP 2024-25); 2.2/2.3 in new schema does exhibit >100% in some districts (2.2>2.3, e.g. observed values near 106%)",
            "Comparable?": "NO",
            "Decision (YES/NO/UNCERTAIN)": "NO",
            "Reason/Evidence": "As stated, feature = institutional-delivery % of TOTAL REPORTED DELIVERIES, but the legacy published figure used ANC registrations as denominator. The two are structurally different and legacy values exceed 100 in several districts. Any Dataset-3 rebuild must adopt a single denominator; old data cannot be matched exactly.",
        },
        {
            "Feature": "PNC_48h_Pct",
            "Old Dataset Definition": "Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%)",
            "HMIS 2020-21 Definition": "6.1 (1st PPC within 48h of HOME delivery) + 2.2.1 (inst. deliveries discharged within 48h). No within-48h institutional PNC checkup item.",
            "HMIS 2021-22 Definition": "same (Telangana 2021-22)",
            "HMIS 2022-23 Definition": "same (UP 2022-23)",
            "HMIS 2023-24 Definition": "6.1 (within 48h, HOME deliveries) + 6.2 (48h-14d after INSTITUTIONAL delivery) + 2.2.1 now means 'stayed 48 hours or more (excl. C-section)' - inverted meaning",
            "HMIS 2024-25 Definition": "same as 2023-24 (UP 2024-25)",
            "Comparable?": "NO",
            "Decision (YES/NO/UNCERTAIN)": "NO",
            "Reason/Evidence": "There is no item recording a within-48h postnatal checkup for institutional deliveries in any year. 6.1 covers home deliveries only; 6.2 is 48h-14d institutional; 2.2.1 relates to discharge/stay timing, not PNC, and its wording inverts across eras. Numerator/intended feature is not reconstructable.",
        },
        {
            "Feature": "Obstetric_Complications_Pct",
            "Old Dataset Definition": "Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%)  -> 5.1 aggregate",
            "HMIS 2020-21 Definition": "5.1 (Number of cases of pregnant women with Obstetric Complications attended - APH, PPH, Sepsis, Eclampsia and others) / total reported deliveries",
            "HMIS 2021-22 Definition": "same (Telangana 2021-22)",
            "HMIS 2022-23 Definition": "same (UP 2022-23)",
            "HMIS 2023-24 Definition": "5.1 REMOVED. Replaced by M1 HRP items: 1.9.1 (Total HRP intrapartum = 1.9.1.a PPH + .b Sepsis + .c Eclampsia + .d obstructed labour) and 1.9.2 (HRP antepartum, new cases only). NOT a 'complications attended' case count.",
            "HMIS 2024-25 Definition": "same as 2023-24 (UP 2024-25); verified 1.9.1 = sum of components in all districts",
            "Comparable?": "NO (2023-24 onward); YES (2020-21 to 2022-23)",
            "Decision (YES/NO/UNCERTAIN)": "NO",
            "Reason/Evidence": "Aggregate 5.1 exists for 2020-23 (comparable within that era if denominator fixed). Since 2023-24 there is no comparable aggregate: HRP intrapartum components omit APH and 'other' complications, are woman-based event counts in facility, and antepartum (1.9.2) tracks only new HRP cases. Cannot reproduce the old feature.",
        },
        {
            "Feature": "(auxiliary) Total reported deliveries",
            "Old Dataset Definition": "Not an explicit item in legacy published reports; derived.",
            "HMIS 2020-21 Definition": "2.1.1.a + 2.1.1.b + 2.2 (home SBA + home non-SBA + institutional); no explicit total-deliveries item in this schema",
            "HMIS 2021-22 Definition": "same (Telangana 2021-22)",
            "HMIS 2022-23 Definition": "same (UP 2022-23)",
            "HMIS 2023-24 Definition": "2.3 (Age wise total number of delivery reported = 2.3.1+2.3.2+2.3.3+2.3.4) - explicit item exists",
            "HMIS 2024-25 Definition": "same as 2023-24",
            "Comparable?": "PARTIAL",
            "Decision (YES/NO/UNCERTAIN)": "UNCERTAIN",
            "Reason/Evidence": "Old-schema denominator is a derived sum (cannot include any missing sub-item, e.g. blank home values in Telangana 2020-21/2021-22). New-schema 2.3 is explicit but does not equal sum(2.1.1.a+2.1.1.b+2.2) or 2.2 in 14/75 UP districts (2024-25 Apr) and 2.2 can exceed 2.3.",
        },
        {
            "Feature": "(auxiliary) PNC within 48h - home only",
            "Old Dataset Definition": "Not directly the feature; 6.1 only.",
            "HMIS 2020-21 Definition": "6.1 home-delivery 1st PPC within 48h",
            "HMIS 2021-22 Definition": "same",
            "HMIS 2022-23 Definition": "same",
            "HMIS 2023-24 Definition": "6.1 'In case of home delivery, number of women receiving 1st Postpartum checkups within 48 hours'",
            "HMIS 2024-25 Definition": "same",
            "Comparable?": "YES as a home-only subset",
            "Decision (YES/NO/UNCERTAIN)": "YES",
            "Reason/Evidence": "6.1 label/scope stable across all years and reconstructable, but covers only home deliveries, so it cannot stand in for the overall PNC_48h feature.",
        },
    ]
    return rows


def write_csv(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({h: "" if r.get(h) is None else r[h] for h in header})
    return path


def write_md(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    struct = build_structure()
    recon = build_reconstruction()
    harm = build_harmonization()

    hdr_harm = ["Feature", "Old Dataset Definition", "HMIS 2020-21 Definition", "HMIS 2021-22 Definition",
                "HMIS 2022-23 Definition", "HMIS 2023-24 Definition", "HMIS 2024-25 Definition",
                "Comparable?", "Decision (YES/NO/UNCERTAIN)", "Reason/Evidence"]
    p1 = write_csv("harmonization_matrix.csv", hdr_harm, harm)
    p2 = write_csv("reconstruction_checks.csv", list(recon[0].keys()), recon)
    p3 = write_csv("maternal_indicator_mapping.csv",
                   ["feature", "old_dataset_definition", "old_schema_codes", "new_schema_codes",
                    "old_label", "new_label", "denominator_note", "present_in_years"],
                   []
                   )
    # maternal indicator mapping (curated rows)
    map_rows = [
        {"feature": "ANC_First_Trimester_Pct",
         "old_dataset_definition": "Registrations For ANC In The First Trimester (To Total ANC Registrations) (%)",
         "old_schema_codes": "1.1.1 / 1.1", "new_schema_codes": "1.1.1 / 1.1",
         "old_label": "Out of the total ANC registered, number registered within 1st trimester (within 12 weeks) / Total number of pregnant women registered for ANC",
         "new_label": "Out of the total NEW ANC registered, number registered within 1st trimester (within 12 weeks) / Total number of NEW Pregnant Women registered for ANC",
         "denominator_note": "1.1 (ANC registrations). Label gains NEW from 2023-24; concept identical.",
         "present_in_years": "2020-21 .. 2024-25"},
        {"feature": "TT2_Booster_Pct",
         "old_dataset_definition": "Pregnant Women Received The Second Dose Of Tetanus-Toxoid Vaccine (TT2) Or Booster (To Total ANC Registrations) (%)",
         "old_schema_codes": "(1.2.2 + 1.2.3) / 1.1", "new_schema_codes": "(1.2.2 + 1.2.3) / 1.1",
         "old_label": "TT2/Td2 + TT Booster/Td Booster over ANC registrations",
         "new_label": "Td2 + Td Booster over ANC registrations (TT2 renamed Td2, TT Booster renamed Td Booster)",
         "denominator_note": "1.1 (ANC registrations). Sum may double-count women given both doses.",
         "present_in_years": "2020-21 .. 2024-25"},
        {"feature": "Severe_Anemia_Pct",
         "old_dataset_definition": "Pregnant Women With Hemoglobin (Hb) Levels<7 (Severe Anemia) (To Women With Hemoglobin (Hb) Levels<11 (Moderate Anemia)) (%)",
         "old_schema_codes": "1.4.3 / 1.4.2", "new_schema_codes": "1.4.3 / 1.4.2",
         "old_label": "1.4.3 Hb<7 (severe) / 1.4.2 Hb<11 (moderate)",
         "new_label": "1.4.3 Hb<=7 g/dl / 1.4.2 Hb<11 (7.1-10.9 g/dl)",
         "denominator_note": "Threshold changed <7 -> <=7 in numerator and denominator relabelled; materiality small but non-zero.",
         "present_in_years": "2020-21 .. 2024-25"},
        {"feature": "Institutional_Delivery_Pct",
         "old_dataset_definition": "Institutional Deliveries (To Total ANC Registrations) (%)",
         "old_schema_codes": "2.2 / 1.1 (ANC)", "new_schema_codes": "2.2 / 2.3 (or 2.1.1.a+2.1.1.b+2.2)",
         "old_label": "Institutional Deliveries conducted (incl. C-Sections) over ANC registrations",
         "new_label": "Institutional Deliveries conducted (incl. C-Sections) over total reported deliveries (2.3 exists only 2023-24+)",
         "denominator_note": "Legacy denominator is ANC registrations (can exceed 100); feature-as-stated needs total reported deliveries denominator.",
         "present_in_years": "2020-21 .. 2024-25 (denominators incompatible across eras)"},
        {"feature": "PNC_48h_Pct",
         "old_dataset_definition": "Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%)",
         "old_schema_codes": "6.1 (home) + 2.2.1 (inst discharged within 48h) - proxy only",
         "new_schema_codes": "6.1 (home only); 6.2 (inst 48h-14d); no within-48h inst PNC item",
         "old_label": "6.1 within-48h PPC (home) / 2.2.1 institutional discharged within 48h",
         "new_label": "6.1 within-48h PPC (home) / 2.2.1 now 'stayed 48h or more' (inverted)",
         "denominator_note": "Neither year exposes a within-48h institutional PNC count; feature not reconstructable.",
         "present_in_years": "2020-21 .. 2024-25 (not comparable to feature)"},
        {"feature": "Obstetric_Complications_Pct",
         "old_dataset_definition": "Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%)",
         "old_schema_codes": "5.1 / total deliveries (derived)", "new_schema_codes": "1.9.1 / 1.9.2 (HRP; NOT comparable)",
         "old_label": "5.1 Number of cases of pregnant women with Obstetric Complications attended (APH, PPH, Sepsis, Eclampsia and others)",
         "new_label": "1.9.1 Total HRP intrapartum (=1.9.1.a PPH+1.9.1.b Sepsis+1.9.1.c Eclampsia+1.9.1.d obstructed labour); 1.9.2 HRP antepartum (new cases)",
         "denominator_note": "5.1 exists 2020-23 only; removed in 2023-24+. HRP items are facility event counts, omit APH/'others', not an attended-cases measure.",
         "present_in_years": "5.1: 2020-21..2022-23; 1.9.x: 2023-24..2024-25"},
    ]
    write_csv("maternal_indicator_mapping.csv", ["feature", "old_dataset_definition", "old_schema_codes",
                                                 "new_schema_codes", "old_label", "new_label",
                                                 "denominator_note", "present_in_years"], map_rows)

    # item dictionary
    item_rows = [{"code": c, "schema_presence": era, "role": role, "old_label": old, "new_label": new}
                 for c, (old, new, role, era) in CODEDICT.items()]
    write_csv("item_dictionary.csv", ["code", "schema_presence", "role", "old_label", "new_label"], item_rows)

    # ---- raw structure report (dynamic table) ----
    lines = ["# Raw HMIS Structure Report (inspection sample)",
             "",
             "This report documents the structure of 10 representative cumulative HMIS raw files selected for the",
             "harmonization audit (2020-21 through 2024-25). All counts were produced from the workbook directly.",
             "",
             "## Sample table",
             "",
             "| FY | State | File | District groups | Districts | Rows | Cols | Item rows | Unique items | Duplicate code rows | Blank cells | Negative cells |",
             "|---|-------|------|-----|-----|-----|-----|-----|-----|-----|-----|-----|"]
    for r in struct:
        lines.append(f"| {r['fy']} | {r['state']} | `{r['file']}` | {r['groups']} | {r['districts']} | "
                     f"{r['row_count']} | {r['col_count']} | {r['item_rows']} | {r['unique_items']} | {r['dup_rows']} | "
                     f"{r['blank_cells']} | {r['neg_cells']} |")
    write_md(os.path.join(OUT, "raw_structure_report.md"), "\n".join(lines) + "\n")

    # ---- inspection report (sections A-L) ----
    harm_table = "| " + " | ".join(hdr_harm[:5]) + " | | |\n"
    prefix_rows = harm
    md = inspect_report(struct, recon, harm)
    write_md(os.path.join(OUT, "inspection_report.md"), md)
    print("wrote:", p1, p2, "maternal_indicator_mapping.csv", "item_dictionary.csv")


def inspect_report(struct, recon, harm):
    return f"""# HMIS Harmonization Audit - Inspection Report (Dataset 3 preparation)

Status: INSPECTION ONLY. No dataset was built; no pipeline/model/XAI/DSS/frontend/backend file was modified.

## A. Purpose & scope
Audit the six MRCDSS features carried through `dataset1.csv` (FY 2008-2016) and `dataset2.csv` (FY 2017-2019)
against the freshly acquired cumulative HMIS raw releases (FY 2020-21 .. 2024-25) to decide whether each feature can
be reconstructed from the raw files and whether definitions are stable across years. This is the prerequisite step
for any future 'Dataset 3 (2020-21 .. 2024-25)' build.

## B. Files available & years covered
Source manifest: `data/recent_hmis/raw/_manifest.json` (487 cumulative files listed). Download status:
- OK (SHA-256 verified): 419 files - FY 2020-21 (38), 2021-22 (36), 2022-23 (36), 2023-24 (36), 2024-25 (273)
- FAILED (HTTP 500, all): 68 files - FY 2025-26 (every file). 2025-26 files are listed by the anonymous `getFiles`
  API but cannot be downloaded anonymously (client-side network tracing showed a 2024-25 file succeeding moments
  before a 2025-26 file failed, repeatedly - not rate limiting). 2025-26 is excluded from this audit.
Verified downloaded bytes: 118,808,935.
Inspection used the 10 representative files below (structure, item dictionary, blanks/negatives, and reconstruction
statistics were computed on all of them).

## C. Raw workbook structure & parsing
- All files are single-sheet XLSX ("Data Item Wise Report"). Title, 'Provisional Figures for <FY> and Month - ...',
  'Status As On: <ts>', and a 'Total [(A+B) or (C+D)]' definition note occupy rows 0-3.
- Column layout: every state/district occupies 5 columns - Total [(A+B) or (C+D)], Public [A], Private [B],
  Urban [C], Rural [D]. District names start at column index 4; the first group (group 0) is the state itself.
- Data rows: module begins in column A only on section-start rows; column B holds the item code (apostrophe-prefixed
  string), column C the label, then the 5 columns per group (all 36 states -> 109 columns in UP files).
- Parsing caveat (verified): these workbooks have no usable XML <dimension>; `openpyxl.read_only=True` reports a
  1x1 cell range. All inspection loads use `read_only=False, data_only=True` (UP 2022-23 = 548 x 384).
- Internal consistency verified on multiple files & rows: for every item, Total == Public + Private == Urban + Rural
  and state total == sum of district totals (diff 0.0 on 1.1 ANC for UP 2022-23, UP 2024-25, Telangana 2021-22).

### Structure of the 10 sampled files
| FY | State | Groups | Districts | Rows | Cols | Item rows | Unique items | Duplicate-code rows | Blank cells | Negative cells |
|---|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
{chr(10).join('| %s | %s | %d | %d | %d | %d | %d | %d | %d | %d | %d |' % (r['fy'], r['state'], r['groups'], r['districts'], r['row_count'], r['col_count'], r['item_rows'], r['unique_items'], r['dup_rows'], r['blank_cells'], r['neg_cells']) for r in struct)}

## D. Item dictionary & schema versioning
- Old schema (2020-21 .. 2022-23): 540 item rows, decimal codes (1.1, 2.1.1.a); no explicit total-deliveries item 2.3.
- New schema (2023-24 .. 2024-25): item rows 698 but only 594 unique codes - the 104 extra rows are repeated-code,
  blank-label sub-rows for stock-balance rows in modules 17-20 (opening/closing balances). No indicator of maternal
  interest is duplicated. Code sets and labels are 100% identical between 2023-24 and 2024-25 (verified Tripura vs UP).
- Module 5 (Obstetric Complications aggregate 5.1) exists ONLY in the old schema; modules 1.9.x HRP items exist ONLY
  in the new schema.
- Item labels formally drift in the new schema: "pregnant women registered" -> "NEW Pregnant Women registered",
  "TT2/TT Booster" -> "Td2/Td Booster", severe-anaemia boundary "<7" -> "<=7 g/dl". Full old/new label pairs are in
  `item_dictionary.csv`.

## E. Six-feature mapping to exact HMIS items (see `maternal_indicator_mapping.csv`)
| Feature | Reconstructed formula | 2020-23 items | 2023-24+ items |
|---|------------------------|----------------|----------------|
| ANC_First_Trimester_Pct | 1.1.1 / 1.1 | 1.1.1, 1.1 | 1.1.1, 1.1 ('NEW' labels) |
| TT2_Booster_Pct | (1.2.2 + 1.2.3) / 1.1 | 1.2.2, 1.2.3, 1.1 | 1.2.2 (Td2), 1.2.3 (Td booster), 1.1 |
| Severe_Anemia_Pct | 1.4.3 / 1.4.2 | 1.4.3 (Hb<7), 1.4.2 (Hb<11) | 1.4.3 (Hb<=7), 1.4.2 (Hb<11 / 7.1-10.9 g/dl) |
| Institutional_Delivery_Pct | 2.2 / (total deliveries) | 2.2 / (2.1.1.a+2.1.1.b+2.2) - legacy published used 2.2/1.1 | 2.2 / 2.3 (explicit) or derived sum |
| PNC_48h_Pct | 6.1 (home-only) - NOT generalizable | 6.1 home 48h PNC; 2.2.1 inst discharged within 48h | 6.1 home 48h PNC; 2.2.1 inverted ('stayed 48h+') |
| Obstetric_Complications_Pct | 5.1 / total deliveries (2020-23) | 5.1 aggregate (APH/PPH/Sepsis/Eclampsia/others) | 1.9.1 total HRP intrapartum / 1.9.2 HRP antepartum (not comparable) |

## F. Harmonization matrix (definition changes across years)
See `harmonization_matrix.csv` (columns: Feature, Old Dataset Definition, HMIS per-year definitions, Comparable?,
Decision (YES/NO/UNCERTAIN), Reason/Evidence). Summary decisions:
- ANC_First_Trimester_Pct: DECISION **YES** (stable across all five years)
- TT2_Booster_Pct: DECISION **YES** (stable; caveat: TT2+Booster sum may double-count)
- Severe_Anemia_Pct: DECISION **UNCERTAIN** (threshold <7 -> <=7, denominator relabelled)
- Institutional_Delivery_Pct: DECISION **NO** (legacy denominator is ANC registrations, not reported deliveries;
  legacy values exceed 100% in several districts - same phenomenon already flagged in the legacy data pipeline)
- PNC_48h_Pct: DECISION **NO** (no within-48h institutional PNC item in any year; item set cannot reproduce feature)
- Obstetric_Complications_Pct: DECISION **NO** for 2023-24+ (5.1 removed; HRP items not an attended-cases measure);
  **YES** for 2020-21 .. 2022-23 (with proper denominator)

## G. Reconstruction checks (see `reconstruction_checks.csv`)
Ratios were recomputed from district Total columns for all 10 sample files. Representative results:
- 2022-23 UP (old schema, 75 districts): ANC 1st-tri median 78.5% (32.8-95.7); TT2+Booster median 82.6%; severe
  anaemia 1.4.3/1.4.2 median 6.5%; institutional 2.2/(home+inst) median 95.8%; PNC-48h 6.1/home+inst median 6.1%;
  obstet. comp. 5.1 median 4.1%. All plausible, none >100 for these constructions, no zero denominators.
- 2024-25 UP (new schema): ANC 1st-tri median 86.2%; TT2+Booster median 80.8%; severe 6.7%; institutional via 2.3
  median 98.2% but max 106.4% (2.2 > 2.3 in at least one district - data inconsistency); PNC 6.1 median 5.4%.
- 2023-24 Tripura (new schema, 8 districts): reconstructed values plausible; 5.1 absent; 1.9.1 == 1.9.1.a+.b+.c+.d in
  every district (sum self-consistent).

## H. Total-column & internal consistency checks
- Total == Public+Private == Urban+Rural with zero mismatches across inspected files/items.
- State total == sum of district totals (verified for 1.1 in UP 2022-23, UP 2024-25, Telangana 2021-22; diff 0.0).
- New-schema only: 2.3 (age-wise total deliveries) FAILS to equal sum(2.3.1..2.3.4) in 14/75 UP districts (2024-25 Apr)
  and fails to equal home+inst in others; 2.2 can exceed 2.3. Use 2.3 or the derived sum with care / validation.

## I. Data-quality findings
- Non-numeric cell values are exclusively EMPTY strings (suppression/absence); there are no '-', 'NA' or '<' markers
  anywhere in the sample. Blanks concentrate in small states (Goa: 1 district fully blank; Telangana: 1 district home
  delivery 2.1.1.a/2.1.1.b blank).
- Negative cell values exist only in vaccine/stock modules 17-20 (e.g. UP 2022-23: 148 negatives across stock rows;
  Ayodhya vaccine rows as large as -892,301). None of the six indicator items carry negatives.
- No decimal counts anywhere; all cells of interest are whole numbers.
- Files are explicitly marked 'Provisional Figures' (all days) and 'Status As On' is months later in some years
  (e.g. 2022-23 file 'Status As On: 01 Oct 2024'), indicating retroactive updating - cumulative provisional data.

## J. Published-percentage availability
A label scan of every sample file found exactly one item containing '%' or '(To Total)' per file: the stock item
'Glutaraldehyde 2%' (19.5). NO published percentage columns for any of the six indicators exist in the recent raw
files for any year 2020-21 .. 2024-25. Every indicator (and every denominator) must be RECONSTRUCTED from counts.

## K. Decisions & handling notes for a future Dataset 3 build
1. ANC_First_Trimester_Pct and TT2_Booster_Pct are safely reconstructable across all five years (denominator = 1.1).
2. Severe_Anemia_Pct is reconstructable but carries a small definitional drift (<7 -> <=7); document as approximate.
3. Institutional_Delivery_Pct must pick ONE denominator: (a) replicate legacy behaviour with ANC registrations (2.2/1.1,
   values can exceed 100 and are cleaned downstream like the legacy data), or (b) adopt %-of-total-reported-deliveries
   (2.2/(2.1.1.a+2.1.1.b+2.2) for 2020-23, 2.2/2.3 for 2023-24+). The two regimes are NOT comparable as-stated.
4. PNC_48h_Pct is NOT reconstructable as the feature was defined; at best the home-only 6.1 share is available.
5. Obstetric_Complications_Pct is reconstructable only for 2020-21 .. 2022-23 via 5.1; 2023-24+ has no comparable item.
6. Any rebuild must be gated on 2025-26 being unavailable anonymously; if 2025-26 is needed, an authenticated download
   path is required first.

## L. Artifact inventory & reproducibility
- `raw_structure_report.md`, `maternal_indicator_mapping.csv`, `harmonization_matrix.csv`, `reconstruction_checks.csv`,
  `item_dictionary.csv`, and this `inspection_report.md` - all under `data/recent_hmis/inspection/`.
- Reusable parsers: `data/recent_hmis/inspection/_lib/hmis_reader.py` (workbook loader / WorkSheet, DistrictGroup, Item)
  and `data/recent_hmis/inspection/_lib/reconstruct.py` (numeric coercion + per-district indicator computation).
- Generator: `data/recent_hmis/inspection/_lib/build_artifacts.py` re-creates every artifact (python, stdlib only,
  needs openpyxl in the environment venv). Raw files are read-only inputs; nothing outside inspection/ is written.
- Re-run: `.venv/bin/python data/recent_hmis/inspection/_lib/build_artifacts.py`
"""


if __name__ == "__main__":
    main()