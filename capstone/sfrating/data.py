"""Loading the book's datasets (Chapter 4)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("SFCM_DATA", "data"))


def _path(name: str) -> Path:
    return DATA_DIR / name


def load_loans() -> pd.DataFrame:
    """Static loan tape of the Thamesbridge pool at the cut-off date."""
    return pd.read_csv(_path("rmbs_loans.csv"),
                       parse_dates=["origination_date", "product_end_date"])


def load_performance() -> pd.DataFrame:
    """Monthly status and balances, one row per loan per month."""
    return pd.read_csv(_path("rmbs_performance.csv.gz"))


def load_defaults() -> pd.DataFrame:
    """One row per defaulted loan with exposure, recovery and loss."""
    return pd.read_csv(_path("rmbs_defaults.csv"))


def load_macro() -> pd.DataFrame:
    return pd.read_csv(_path("macro.csv"))


def load_deal() -> dict:
    return json.loads(_path("rmbs_deal.json").read_text())


def load_cmbs() -> pd.DataFrame:
    return pd.read_csv(_path("cmbs_loans.csv"))


def load_auto() -> pd.DataFrame:
    return pd.read_csv(_path("auto_loans.csv"))


def load_clo() -> pd.DataFrame:
    return pd.read_csv(_path("clo_portfolio.csv"))


def load_rating_table() -> pd.DataFrame:
    return pd.read_csv(_path("rating_default_table.csv"))


def load_rating_stresses() -> pd.DataFrame:
    return pd.read_csv(_path("rating_stresses.csv"))
