# Progress

## Current status

- **Week:** 1 of 8.5 (16–22 Nov 2026) — Foundations, **completed**; week 2 starts 23 Nov
- **Last updated:** 2026-11-17

## Week 1 — Foundations

**Done when:** the files are in the `landing` Volume and the bundle deploys an empty job.

| Task | Status |
| --- | --- |
| Inspect local data (folders, file names, column counts vs. layout, cut-off date) | Done — see [`data_profile.md`](data_profile.md) |
| Repository skeleton, `.gitignore`, `pyproject.toml`, minimal `databricks.yml` | Done |
| Confirm the Databricks workspace plan | Done — Free Edition (limits below) |
| Default definition | Done — [ADR 0001](decisions/0001-default-definition.md) |
| Scripts to create catalog/schemas/Volume and upload samples (`scripts/`) | Written, dry-run only |
| Install the Databricks CLI and authenticate (user) | Done — CLI v1.26.0, profile `DEFAULT` |
| Catalog `credit` | Done — created manually in the UI with Default Storage (documented in README) |
| Schemas `bronze`, `silver`, `gold`, `ml` and Volume `credit.bronze.landing` | Done — `scripts/setup_catalog.sh` |
| Upload vintages 2005, 2006, 2007, 2019 (≈1.3 GB) | Done — 8 files, sizes match local copies |
| Empty job in `resources/`, `bundle validate`, `bundle deploy -t dev` | Done — job `[dev danivasgo2702] credit-engine` |
| Push to GitHub | Done |

**Week 1 done criterion: met** (2026-11-17). Files are in the `landing` Volume and the bundle
deployed an empty job.

## Decisions

- **Data location:** raw files live outside the repo at `~/Documents/data/freddie_mac/`.
  `.gitignore` blocks data folders and every Freddie Mac file pattern.
- **Vintage = origination year**, taken from the loan identifier (`PYYQnXXXXXXX`), not from
  the first payment date (~16% of loans have their first payment in the following year).
- **Performance cut-off = 2026-06.** Vintages 2005–2023 have a complete 24-month window;
  2024 is partial (41.9%); 2025–2026 are "production" data.
- **Default label:** first event within 24 months among status `>= 03`, `RA`, or zero-balance
  code `02/03/09/15`; prepayment before that is a non-default (ADR 0001).
- **Workspace = Databricks Free Edition:** serverless compute only, one 2X-Small SQL
  warehouse, **one active Lakeflow pipeline per type**, max 5 concurrent job tasks, no custom
  storage locations, daily usage quota. The console does not support automated browser
  control, so all Databricks work goes through the CLI and the bundle.
  - Consequence: Bronze, Silver and Gold must live in **one** Lakeflow Declarative Pipeline.
  - Catalog creation through the CLI/API fails (*"Metastore storage root URL does not
    exist…"*), but UI creation with Default Storage works. **Decision:** keep the catalog
    `credit`, created once by hand in the UI; `scripts/setup_catalog.sh` only checks that it
    exists and creates the schemas and the Volume. Using `workspace` was rejected to keep
    the project isolated and the table names (`credit.gold.*`) as designed.
  - Not yet verified: Lakehouse Monitoring availability (week 7).
- **Landing layout:** `/Volumes/credit/bronze/landing/freddie_mac/{origination,performance}/`.
  One folder per file type, so each Auto Loader stream reads files with a single schema.
- **Week 1 upload subset:** only 2005, 2006, 2007 and 2019 while the pipeline is built
  (crisis vintages + one test vintage, and stays well inside the free quota).
- **Dependencies are added per week**: `pyproject.toml` starts with only `pytest` (dev).
- **Git workflow** (ADR 0002): `develop` created from `main`; all new work goes in
  `feature/`, `fix/`, `test/`, `docs/` or `chore/` branches with a pull request to
  `develop`, squash-merged by the owner. `main` only receives the final `v1.0.0`.

## Open questions

### COVID forbearance and disaster delinquency (to decide in week 4)

The performance file has three relevant fields: **Payment Deferral Flag** (field 25,
`C`/`P`), **Delinquency Due to Disaster** (field 29, `Y`, from Jan 2014) and **Borrower
Assistance Plan** (field 30, `F` forbearance, `R` repayment, `T` trial, from Jan 2014).
Measured with the ADR 0001 rule on the local samples:

| Vintage | 24-month default rate | Defaults flagged F or Y at the event | Defaults that later return to `00` |
| --- | ---: | ---: | ---: |
| 2016 | 0.66% | 40% | 78% |
| 2017 | 0.79% | 33% | 77% |
| 2018 | 2.56% | 79% | 86% |
| 2019 | 4.58% | 93% | 90% |
| 2020 | 1.62% | 86% | 91% |
| 2021 | 0.93% | 64% | 89% |
| 2022 | 1.78% | 42% | 81% |

The problem is not only 2020–2021: the windows of **2018 and 2019** overlap the 2020
forbearance wave, and 2019 is the first test vintage.

**Decision (2026-11-17):** in week 4 the **primary label is the forbearance-adjusted label**
(point 2 below) and the original ADR 0001 label is kept as a **sensitivity** label. Recorded
as an amendment in ADR 0001.

Treatment (not implemented yet):

1. Keep the ADR 0001 rule as the sensitivity label, and add a **flag
   `default_in_forbearance`** when the first default month has `F` in field 30 or `Y` in
   field 29.
2. Build the **adjusted (primary) label** that ignores DQ90 events flagged as
   forbearance/disaster unless the loan later hits a credit-event zero-balance code
   (`02/03/09/15`) or `RA`.
3. Train on 2005–2015 (unaffected), and report test metrics for 2019 **with both labels**,
   plus a 2017 hold-out as a pre-COVID reference.
4. In the drift report (week 7), treat 2020–2021 as a known regime shift rather than a model
   failure.

## Next steps

Week 2 (23–29 Nov) — Bronze with Auto Loader:

1. Origination and performance schemas in `src/credit_engine/schemas/` from the July 2026
   layout (31 and 35 columns), with tests.
2. Bronze ingestion with Auto Loader from `landing/freddie_mac/{origination,performance}`,
   adding `_ingest_ts`, `_source_file`, `_vintage`, inside the single Lakeflow pipeline
   allowed by Free Edition.
3. Script that drops one month of performance data at a time.
4. Done when a new file appears in Bronze and re-running does not duplicate rows.
