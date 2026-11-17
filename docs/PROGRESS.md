# Progress

## Current status

- **Week:** 1 of 8.5 (16–22 Nov 2026) — Foundations
- **Last updated:** 2026-11-16

## Week 1 — Foundations

**Done when:** the files are in the `landing` Volume and the bundle deploys an empty job.

| Task | Status |
| --- | --- |
| Inspect local data (folders, file names, column counts vs. layout, cut-off date) | Done — see [`data_profile.md`](data_profile.md) |
| Repository skeleton, `.gitignore`, `pyproject.toml`, minimal `databricks.yml` | Done |
| First commit | Done |
| Confirm the Databricks workspace plan (serverless only? Unity Catalog? Lakehouse Monitoring?) | Pending |
| Install / configure the Databricks CLI (user handles authentication) | Pending |
| Create catalog `credit` with schemas `bronze`, `silver`, `gold`, `ml`, and Volume `landing` | Pending |
| Script to upload the sample files to the Volume (`scripts/`) | Pending |
| Empty job in `resources/` and first `databricks bundle deploy` | Pending |

## Decisions

- **Data location:** raw files live outside the repo at `~/Documents/data/freddie_mac/`
  (`CLAUDE.md` still says `~/data/freddie_mac/`). `.gitignore` blocks data folders and
  every Freddie Mac file pattern.
- **Vintage = origination year**, taken from the loan identifier (`PYYQnXXXXXXX`), not from
  the first payment date (~16% of loans have their first payment in the following year).
- **Performance cut-off = 2026-06** (last `Period` in every performance file). A loan has a
  complete 24-month window only if `first_payment_date + 23 months <= 2026-06`. Vintages
  2005–2023 are complete; 2024 is partially complete; 2025–2026 are "production" data.
- **Dependencies are added per week**: `pyproject.toml` starts with only `pytest` (dev);
  Spark, LightGBM, MLflow and PuLP are added in the week that uses them.
- **`databricks.yml` has no job yet**: compute settings depend on the workspace plan, which
  is still unconfirmed.

## Open questions

- Which Databricks workspace/plan is used (Free Edition, trial, paid)? This decides
  serverless vs. classic compute and whether Lakehouse Monitoring is available.
- Default label (week 4): 90+ days delinquent (`status >= 03` or `RA`) **or** a credit-event
  zero-balance code (`02`, `03`, `09`, `15`) within 24 months — to be confirmed.

## Next steps

1. Confirm the workspace plan and install the Databricks CLI.
2. Create the catalog, schemas and `landing` Volume.
3. Upload the sample files to the Volume and deploy an empty job with the bundle.
