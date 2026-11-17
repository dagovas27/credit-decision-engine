# Data profile — Freddie Mac SFLLD sample (Release 48, October 2026)

Inspection run on 2026-11-16 over the local copy at `~/Documents/data/freddie_mac/`.
Only aggregate statistics are recorded here; no raw records.

## Files

- 22 folders, `sample_2005` … `sample_2026`, each with exactly two files:
  `sample_orig_YYYY.txt` (origination) and `sample_perf_YYYY.txt` (monthly performance).
- Plus `file_layout_july_2026.xlsx` and `user_guide.pdf`. Total size ≈ 6.4 GB.
- Pipe-delimited, no header row, no trailing delimiter.

## Column counts vs. layout

| File type | Columns in layout | Columns found | Rows with another count |
| --- | --- | --- | --- |
| Origination | 31 | 31 in every file | 0 |
| Performance | 35 | 35 in every file | 0 |

The last origination field is **VantageScore 4.0** (field 31) and the last performance field
is **Bankruptcy Cramdown Costs** (field 35, usually empty, which is why lines end in `|`).
Schemas must be built from the July 2026 layout, not from older tutorials.

## Row counts and date ranges

| Vintage | Loans | Performance rows | Period range | Loans with full 24-month window |
| --- | ---: | ---: | --- | ---: |
| 2005 | 50,000 | 3,880,689 | 2005-01 … 2026-06 | 100% |
| 2006 | 50,000 | 3,206,738 | 2006-01 … 2026-06 | 100% |
| 2007 | 50,000 | 3,015,985 | 2006-12 … 2026-06 | 100% |
| 2008 | 50,000 | 2,459,814 | 2008-01 … 2026-06 | 100% |
| 2009 | 50,000 | 3,166,993 | 2009-01 … 2026-06 | 100% |
| 2010 | 50,000 | 3,455,416 | 2010-01 … 2026-06 | 100% |
| 2011 | 50,000 | 3,645,574 | 2011-01 … 2026-06 | 100% |
| 2012 | 50,000 | 4,538,907 | 2012-01 … 2026-06 | 100% |
| 2013 | 50,000 | 4,228,916 | 2013-01 … 2026-06 | 100% |
| 2014 | 50,000 | 3,420,282 | 2014-01 … 2026-06 | 100% |
| 2015 | 50,000 | 3,501,425 | 2015-01 … 2026-06 | 100% |
| 2016 | 50,000 | 3,421,458 | 2016-01 … 2026-06 | 100% |
| 2017 | 50,000 | 2,837,053 | 2017-01 … 2026-06 | 100% |
| 2018 | 50,000 | 2,089,132 | 2018-01 … 2026-06 | 100% |
| 2019 | 50,000 | 1,977,122 | 2019-01 … 2026-06 | 100% |
| 2020 | 50,000 | 2,611,030 | 2020-01 … 2026-06 | 100% |
| 2021 | 50,000 | 2,657,066 | 2021-01 … 2026-06 | 100% |
| 2022 | 50,000 | 2,151,863 | 2022-01 … 2026-06 | 100% |
| 2023 | 50,000 | 1,567,055 | 2023-01 … 2026-06 | 99.9% |
| 2024 | 50,000 | 1,074,005 | 2024-01 … 2026-06 | 41.9% |
| 2025 | 50,000 | 541,883 | 2025-01 … 2026-06 | 0% |
| 2026 | 25,000 | 63,330 | 2026-01 … 2026-06 | 0% |

"Full 24-month window" = `first_payment_date + 23 months <= 2026-06`.

**Performance cut-off: 2026-06.** It is the last `Period` in every performance file. The user
guide does not state the cut-off date (it refers to the release notes), so the data is the
source of truth. 2026 is a partial vintage (25,000 loans, originations up to roughly June 2026).

## Vintage definition

The vintage is the **origination year**, encoded in the loan identifier `PYYQnXXXXXXX`
(`YYQn` = origination year and quarter); it matches the folder year for 100% of loans.
The first payment date is in the following year for ~16% of loans (December originations),
and a handful of relief-refinance/modified loans have first payment dates years later.

## Delinquency status (user guide)

`Current Loan Delinquency Status` (performance field 4) counts days past due from the
Due Date of Last Paid Installment (DDLPI):

| Code | Meaning |
| --- | --- |
| `00` | Current or < 30 days delinquent (for periods ≤ 2025-09 it can also mean "before first payment") |
| `01` | 30–59 days |
| `02` | 60–89 days |
| `03` | 90–119 days, and so on in 30-day buckets, capped at `99` |
| `RA` | REO acquisition |
| `XX` | Not available |

The field is a string, not a number (`RA`, `XX`). Observed values in 2007 and 2020 are
`00`–`99` and `RA`.

**90+ days delinquent** therefore means `status >= 03` (numeric) or `status = RA`.

## Termination events and losses

- Zero balance codes: `01` prepaid/matured, `02` third-party sale, `03` short sale/charge-off,
  `09` REO disposition, `15` whole-loan sale, `16` reperforming-loan securitisation,
  `96` confirmed defect before a credit event.
- Actual loss is calculated only for codes `02`, `03`, `09`, `15`, is null for loans with a
  defect settlement date, and is **null for loans disposed in the three months before the
  cut-off** (2026-04 … 2026-06). Recoveries are negative, expenses positive.
- Accounting cycle changed twice (May 2019 and October 2025); event timing in the
  performance file follows different rules before and after each change.

## Data quality notes (sentinels)

| Field | Sentinel | Example counts |
| --- | --- | --- |
| Classic FICO | `9999` (not available; values outside 300–850 also become 9999) | 41 in 2005, 29 in 2026 |
| DTI | `999` | 1,532 in 2005, 4,020 in 2015 |
| LTV | `999` | ≤ 2 per vintage |

Sentinels must become nulls in Silver, not fail the FICO/LTV/DTI range checks blindly.
