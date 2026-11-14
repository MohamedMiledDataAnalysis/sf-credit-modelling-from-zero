"""Run the Thamesbridge rating model end to end (Chapters 22 and 23).

Usage, from the repository root:

    python capstone/run_rating.py
    python capstone/run_rating.py --sonia 4.0 --output-dir outputs

Steps: load the data, fit the PD model, compute rating-level default
frequency and severity, run the cashflow scenarios, assign model ratings
and write CSV files and a LaTeX report into the output folder.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np

# Make "import sfrating" work with or without "pip install -e capstone"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sfrating import data, pd_model, rating, report, rmbs  # noqa: E402

log = logging.getLogger("run_rating")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Thamesbridge rating model")
    p.add_argument("--data-dir", default=str(data.DATA_DIR),
                   help="folder holding the CSV and JSON files "
                        "(default: $SFCM_DATA, else data)")
    p.add_argument("--output-dir", default="outputs",
                   help="folder for the results and the report")
    p.add_argument("--sonia", type=float, default=3.0,
                   help="SONIA assumption, %% per year")
    p.add_argument("--cprs", type=float, nargs="+", default=[0.05, 0.20],
                   help="annual prepayment rates to test")
    p.add_argument("--severity-factor", type=float, default=1.0,
                   help="multiply every rating-level severity")
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> dict:
    data.DATA_DIR = Path(args.data_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    loans = data.load_loans()
    defaults = data.load_defaults()
    deal = data.load_deal()
    stresses = data.load_rating_stresses()
    log.info("loaded %d loans, pool balance GBP %.1f m",
             len(loans), loans["current_balance"].sum() / 1e6)

    model = pd_model.fit_pd_model(loans, defaults)
    base_pd = pd_model.predict_pd(model, loans)
    flag = pd_model.default_flag(loans, defaults)
    log.info("PD model: mean 5-year PD %.2f%%, Gini %.3f",
             100 * base_pd.mean(), pd_model.gini(flag, base_pd))

    levels = rmbs.rating_level_losses(loans, base_pd, stresses)
    levels["loss_severity"] *= args.severity_factor
    levels["pool_loss"] = (levels["default_frequency"]
                           * levels["loss_severity"])
    log.info("AAA pool loss %.2f%%, B pool loss %.2f%%",
             100 * levels["pool_loss"].iloc[0],
             100 * levels["pool_loss"].iloc[-1])

    term = int(round(np.average(loans["remaining_term_months"],
                                weights=loans["current_balance"])))
    results = rating.scenario_results(deal, levels, remaining_term=term,
                                      cprs=tuple(args.cprs),
                                      sonia_pct=args.sonia)
    ratings = rating.assign_ratings(results)
    log.info("remaining term %d months, %d scenario rows",
             term, len(results))
    log.info("model ratings: %s",
             ", ".join(f"{c} {r}" for c, r in ratings.items()))

    table = ratings.rename_axis("class").reset_index()
    levels.to_csv(out_dir / "rating_levels.csv", index=False)
    results.to_csv(out_dir / "scenario_results.csv", index=False)
    table.to_csv(out_dir / "model_ratings.csv", index=False)

    # LaTeX reads "_" as a subscript: use spaces in the report headers
    def latex_safe(df):
        return df.rename(columns=lambda c: c.replace("_", " "))

    tex = report.write_report(
        out_dir / "model_report.tex",
        title="Thamesbridge Mortgages No. 1: model ratings",
        author="Mohamed Miled", date=r"\today",
        purpose="Teaching rating model for a fictional UK RMBS.",
        levels=latex_safe(levels), ratings=latex_safe(table),
        limitations="Illustrative stresses; representative-line "
                    "cashflows; in-sample PD model.")
    log.info("wrote %s", tex)
    return {"levels": levels, "results": results, "ratings": ratings,
            "remaining_term": term}


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    run(parse_args(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
