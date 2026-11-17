# Credit Decision Engine

Predicts the probability of default (PD) of single-family mortgages and decides whether to
approve each loan by maximising expected profit under a portfolio loss limit. Built as a
Medallion lakehouse (Bronze → Silver → Gold) on Databricks with MLflow and Asset Bundles.

> Work in progress. See [`docs/PROGRESS.md`](docs/PROGRESS.md) for the current status.

## Data

This project uses the **Freddie Mac Single-Family Loan-Level Dataset** (sample files).
The data is **not** included in this repository: Freddie Mac's terms do not allow
redistribution.

To reproduce:

1. Register for free at Freddie Mac Clarity Data Intelligence and open the SFLLD
   *Data Download* section.
2. Download the yearly sample archives (`sample_YYYY.zip`), the file layout
   (`file_layout_*.xlsx`) and the general user guide.
3. Unzip them outside the repository, e.g. `~/Documents/data/freddie_mac/sample_YYYY/`.
   Each folder contains `sample_orig_YYYY.txt` and `sample_perf_YYYY.txt`
   (pipe-delimited, no header).

## Development

```bash
uv sync
uv run pytest
```
