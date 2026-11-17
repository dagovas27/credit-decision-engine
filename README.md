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

## Databricks setup

The project targets **Databricks Free Edition** (serverless only) and is deployed with a
Databricks Asset Bundle.

1. Install the [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/install)
   and authenticate: `databricks auth login --host <workspace-url>` (save it as the
   `DEFAULT` profile).
2. **Manual step, once:** create the catalog `credit` in the UI
   (*Catalog* → *Create catalog*, storage: *Default Storage*). Free Edition does not allow
   creating catalogs through the API or CLI.
3. Create the schemas and the landing Volume: `scripts/setup_catalog.sh`
4. Upload sample vintages: `scripts/upload_samples.sh 2005 2006 2007 2019`
5. Deploy: `databricks bundle validate && databricks bundle deploy -t dev`

Both scripts accept `DRY_RUN=1` to print the commands without running them.

## Development

```bash
uv sync
uv run pytest
```
