# MRCDSS — HMIS Recent-Series Acquisition Report

Generated: 2026-09-21T14:51:11.778694+00:00
Manifest: `/Users/amulyapagidimarri/Desktop/MRCDSS/data/recent_hmis/raw/_manifest.json`
Raw root: `/Users/amulyapagidimarri/Desktop/MRCDSS/data/recent_hmis/raw`

## Summary

- Target files (canonical enumeration): **487**
- Downloaded: **419**  ·  Skipped (already present): **0**  ·  Failed: **68**
- Downloaded bytes on disk (SHA-verified): **118,808,935**
- Every downloaded file passed SHA-256 verification against the manifest.
- Scope per agreed plan: `B.Cummulative` only; `A.MonthWise` intentionally not fetched; 2020-21..2023-24 limited to `UpTo_Mar`; 2024-25 & 2025-26 kept every published cumulative file.

## 2025-2026

- Enumerated: **68**  ·  Downloaded: **0**  ·  Failed: **68**
- States of failed files: **23** (Andaman & Nicobar Islands, Arunachal Pradesh, Bihar, Chandigarh, Delhi, Goa, Haryana, Himachal Pradesh, Jammu and Kashmir, Kerala, Ladakh, Lakshadweep, Manipur, Meghalaya, Mizoram, Nagaland, Puducherry, Punjab, Sikkim, Telangana, The Dadra and Nagar Haveli and Daman and Diu, Tripura, Uttarakhand)
- Every failed file returned **HTTP 500** deterministically across two independent runs and `curl` probes, even while a 2024-2025 file downloaded successfully seconds apart — i.e. NOT rate-limiting. The 2025-2026 files list in the portal directory but are not served to anonymous downloads (the portal UI also hides this year's folder from anonymous users). Likely requires an authenticated HMIS session. **Not downloaded.**

| State | Files published (UpTo month) — all failed |
| --- | --- |
| Andaman & Nicobar Islands | Jan, Jul, Jun, May, Sep |
| Arunachal Pradesh | Jul |
| Bihar | Jul |
| Chandigarh | Jan, Jul, Jun, Mar, May, Sep |
| Delhi | Jul |
| Goa | Aug, Dec, Jan, Jul, Jun, Mar, May, Sep |
| Haryana | Jul |
| Himachal Pradesh | Jul |
| Jammu and Kashmir | Jul |
| Kerala | Jul |
| Ladakh | Jan, Jul, Jun, May, Sep |
| Lakshadweep | Aug, Dec, Jan, Jul, Jun, Mar, May, Sep |
| Manipur | Jul |
| Meghalaya | Jul |
| Mizoram | Jul, May |
| Nagaland | Jul |
| Puducherry | Jan, Jul, Jun, May, Sep |
| Punjab | Jul |
| Sikkim | Jan, Jul, May |
| Telangana | Jul |
| The Dadra and Nagar Haveli and Daman and Diu | Apr, Aug, Dec, Feb, Jan, Jul, Jun, Mar, May, Nov, Oct, Sep |
| Tripura | Jul |
| Uttarakhand | Jul |

## 2024-2025

- Enumerated: **273**  ·  Downloaded: **273**  ·  Failed: **0**
- States covered: **36**
- Cumulative-month completeness: every published cumulative file kept; see table below.

| State | Cumulative month(s) retained |
| --- | --- |
| Andaman & Nicobar Islands | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Jan, Feb, Mar |
| Andhra Pradesh | Apr, May, Jun, Jul, Aug, Sep |
| Arunachal Pradesh | Apr, May, Jun, Jul, Aug, Sep, Mar |
| Assam | Apr, May, Jun, Jul, Aug, Sep |
| Bihar | Apr, May, Jun, Jul, Aug, Sep |
| Chandigarh | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Jan, Feb, Mar |
| Chhattisgarh | Apr, May, Jun, Jul, Aug, Sep |
| Delhi | Apr, May, Jun, Jul, Aug, Sep, Mar |
| Goa | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Jan, Feb, Mar |
| Gujarat | Apr, May, Jun, Jul, Aug, Sep |
| Haryana | Apr, May, Jun, Jul, Aug, Sep |
| Himachal Pradesh | Apr, May, Jun, Jul, Aug, Sep |
| Jammu and Kashmir | Apr, May, Jun, Jul, Aug, Sep |
| Jharkhand | Apr, May, Jun, Jul, Aug, Sep |
| Karnataka | Apr, May, Jun, Jul, Aug, Sep |
| Kerala | Apr, May, Jun, Jul, Aug, Sep |
| Ladakh | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Feb, Mar |
| Lakshadweep | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Jan, Feb, Mar |
| Madhya Pradesh | Apr, May, Jun, Jul, Aug, Sep |
| Maharashtra | Apr, May, Jun, Jul, Aug, Sep |
| Manipur | Apr, May, Jun, Jul, Aug, Sep, Nov, Mar |
| Meghalaya | Apr, May, Jun, Jul, Aug, Sep, Mar |
| Mizoram | Apr, May, Jun, Jul, Aug, Sep, Nov, Mar |
| Nagaland | Apr, May, Jun, Jul, Aug, Sep, Mar |
| Odisha | Apr, May, Jun, Jul, Aug, Sep |
| Puducherry | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Jan, Feb, Mar |
| Punjab | Apr, May, Jun, Jul, Aug, Sep |
| Rajasthan | Apr, May, Jun, Jul, Aug, Sep |
| Sikkim | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Feb, Mar |
| Tamil Nadu | Apr, May, Jun, Jul, Aug, Sep |
| Telangana | Apr, May, Jun, Jul, Aug, Sep, Mar |
| The Dadra and Nagar Haveli and Daman and Diu | Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Jan, Feb, Mar |
| Tripura | Apr, May, Jun, Jul, Aug, Sep, Mar |
| Uttar Pradesh | Apr, May, Jun, Jul, Aug, Sep |
| Uttarakhand | Apr, May, Jun, Jul, Aug, Sep, Mar |
| West Bengal | Apr, May, Jun, Jul, Aug, Sep |

## 2023-2024

- Enumerated: **36**  ·  Downloaded: **36**  ·  Failed: **0**
- States covered: **36**
- Cumulative-month completeness: **every state UpTo_Mar** ✓

| State | Cumulative month(s) retained |
| --- | --- |
| Andaman & Nicobar Islands | Mar |
| Andhra Pradesh | Mar |
| Arunachal Pradesh | Mar |
| Assam | Mar |
| Bihar | Mar |
| Chandigarh | Mar |
| Chhattisgarh | Mar |
| Delhi | Mar |
| Goa | Mar |
| Gujarat | Mar |
| Haryana | Mar |
| Himachal Pradesh | Mar |
| Jammu and Kashmir | Mar |
| Jharkhand | Mar |
| Karnataka | Mar |
| Kerala | Mar |
| Ladakh | Mar |
| Lakshadweep | Mar |
| Madhya Pradesh | Mar |
| Maharashtra | Mar |
| Manipur | Mar |
| Meghalaya | Mar |
| Mizoram | Mar |
| Nagaland | Mar |
| Odisha | Mar |
| Puducherry | Mar |
| Punjab | Mar |
| Rajasthan | Mar |
| Sikkim | Mar |
| Tamil Nadu | Mar |
| Telangana | Mar |
| The Dadra and Nagar Haveli and Daman and Diu | Mar |
| Tripura | Mar |
| Uttar Pradesh | Mar |
| Uttarakhand | Mar |
| West Bengal | Mar |

## 2022-2023

- Enumerated: **36**  ·  Downloaded: **36**  ·  Failed: **0**
- States covered: **36**
- Cumulative-month completeness: **every state UpTo_Mar** ✓

| State | Cumulative month(s) retained |
| --- | --- |
| Andaman & Nicobar Islands | Mar |
| Andhra Pradesh | Mar |
| Arunachal Pradesh | Mar |
| Assam | Mar |
| Bihar | Mar |
| Chandigarh | Mar |
| Chhattisgarh | Mar |
| Delhi | Mar |
| Goa | Mar |
| Gujarat | Mar |
| Haryana | Mar |
| Himachal Pradesh | Mar |
| Jammu and Kashmir | Mar |
| Jharkhand | Mar |
| Karnataka | Mar |
| Kerala | Mar |
| Ladakh | Mar |
| Lakshadweep | Mar |
| Madhya Pradesh | Mar |
| Maharashtra | Mar |
| Manipur | Mar |
| Meghalaya | Mar |
| Mizoram | Mar |
| Nagaland | Mar |
| Odisha | Mar |
| Puducherry | Mar |
| Punjab | Mar |
| Rajasthan | Mar |
| Sikkim | Mar |
| Tamil Nadu | Mar |
| Telangana | Mar |
| The Dadra and Nagar Haveli and Daman and Diu | Mar |
| Tripura | Mar |
| Uttar Pradesh | Mar |
| Uttarakhand | Mar |
| West Bengal | Mar |

## 2021-2022

- Enumerated: **36**  ·  Downloaded: **36**  ·  Failed: **0**
- States covered: **36**
- Cumulative-month completeness: **every state UpTo_Mar** ✓

| State | Cumulative month(s) retained |
| --- | --- |
| Andaman & Nicobar Islands | Mar |
| Andhra Pradesh | Mar |
| Arunachal Pradesh | Mar |
| Assam | Mar |
| Bihar | Mar |
| Chandigarh | Mar |
| Chhattisgarh | Mar |
| Delhi | Mar |
| Goa | Mar |
| Gujarat | Mar |
| Haryana | Mar |
| Himachal Pradesh | Mar |
| Jammu and Kashmir | Mar |
| Jharkhand | Mar |
| Karnataka | Mar |
| Kerala | Mar |
| Ladakh | Mar |
| Lakshadweep | Mar |
| Madhya Pradesh | Mar |
| Maharashtra | Mar |
| Manipur | Mar |
| Meghalaya | Mar |
| Mizoram | Mar |
| Nagaland | Mar |
| Odisha | Mar |
| Puducherry | Mar |
| Punjab | Mar |
| Rajasthan | Mar |
| Sikkim | Mar |
| Tamil Nadu | Mar |
| Telangana | Mar |
| The Dadra and Nagar Haveli and Daman and Diu | Mar |
| Tripura | Mar |
| Uttar Pradesh | Mar |
| Uttarakhand | Mar |
| West Bengal | Mar |

## 2020-2021

- Enumerated: **38**  ·  Downloaded: **38**  ·  Failed: **0**
- States covered: **38**
- Cumulative-month completeness: **every state UpTo_Mar** ✓

| State | Cumulative month(s) retained |
| --- | --- |
| Andaman & Nicobar Islands | Mar |
| Andhra Pradesh | Mar |
| Arunachal Pradesh | Mar |
| Assam | Mar |
| Bihar | Mar |
| Chandigarh | Mar |
| Chhattisgarh | Mar |
| Dadra & Nagar Haveli | Mar |
| Daman & Diu | Mar |
| Delhi | Mar |
| Goa | Mar |
| Gujarat | Mar |
| Haryana | Mar |
| Himachal Pradesh | Mar |
| Jammu and Kashmir | Mar |
| Jharkhand | Mar |
| Karnataka | Mar |
| Kerala | Mar |
| Ladakh | Mar |
| Lakshadweep | Mar |
| Madhya Pradesh | Mar |
| Maharashtra | Mar |
| Manipur | Mar |
| Meghalaya | Mar |
| Mizoram | Mar |
| Nagaland | Mar |
| Odisha | Mar |
| Puducherry | Mar |
| Punjab | Mar |
| Rajasthan | Mar |
| Sikkim | Mar |
| Tamil Nadu | Mar |
| Telangana | Mar |
| The Dadra and Nagar Haveli and Daman and Diu | Mar |
| Tripura | Mar |
| Uttar Pradesh | Mar |
| Uttarakhand | Mar |
| West Bengal | Mar |

