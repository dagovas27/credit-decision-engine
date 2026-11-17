# Progress

## Current status

- **Week:** 1 of 8.5 (16–22 Nov 2026) — Foundations
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
| Install the Databricks CLI and authenticate (user) | Pending — Homebrew failed: outdated Command Line Tools |
| Run `scripts/setup_catalog.sh` | Pending — needs CLI and approval |
| Upload vintages 2005, 2006, 2007, 2019 (≈1.3 GB) | Pending — needs CLI and approval |
| Empty serverless job in `resources/` and first `databricks bundle deploy` | Pending |

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
  - Not yet verified: catalog creation, Lakehouse Monitoring availability (week 7).
- **Landing layout:** `/Volumes/credit/bronze/landing/freddie_mac/{origination,performance}/`.
  One folder per file type, so each Auto Loader stream reads files with a single schema.
- **Week 1 upload subset:** only 2005, 2006, 2007 and 2019 while the pipeline is built
  (crisis vintages + one test vintage, and stays well inside the free quota).
- **Dependencies are added per week**: `pyproject.toml` starts with only `pytest` (dev).

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
forbearance wave, and 2019 is the first test vintage. Proposed treatment (not implemented):

1. Keep ADR 0001 as the primary label, and add a **flag `default_in_forbearance`** when the
   first default month has `F` in field 30 or `Y` in field 29.
2. Build an **alternative label** that ignores DQ90 events flagged as forbearance/disaster
   unless the loan later hits a credit-event zero-balance code (`02/03/09/15`) or `RA`.
3. Train on 2005–2015 (unaffected), and report test metrics for 2019 **with both labels**,
   plus a 2017 hold-out as a pre-COVID reference.
4. In the drift report (week 7), treat 2020–2021 as a known regime shift rather than a model
   failure.

## Next steps

1. User fixes the Command Line Tools, installs the Databricks CLI and runs `databricks auth login`.
2. With approval: run `scripts/setup_catalog.sh`, then `scripts/upload_samples.sh 2005 2006 2007 2019`.
3. Add an empty serverless job to `resources/` and deploy the bundle.
