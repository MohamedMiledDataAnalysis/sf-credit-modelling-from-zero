"""Turn the raw files of data/raw/ into the model tables of data/.

This is the preparation step of real work: the loan-level data arrive
as the FCA XML report, the servicer reports as Excel workbooks and the
economic series in the layouts of their publishers, and the models
read clean tables. Chapter 4 walks through this file.

    python scripts/prepare_data.py            # from the repository root

Every output is checked: field formats, no-data codes, code lists, and a
reconciliation of the servicer tapes with the investor report.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

import fca_xml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"
ND = {"ND1", "ND2", "ND3", "ND4", "ND5"}
TITLE_ROWS = 4          # Excel reports: 3 title lines and a blank row


def read_report(path: Path, sheet=0) -> pd.DataFrame:
    """Read an Excel report whose table starts after the title block."""
    return pd.read_excel(path, sheet_name=sheet, skiprows=TITLE_ROWS)


def code_lists() -> dict[str, dict[str, str]]:
    """{field code: {list code: model value}} from the data dictionary."""
    codes = pd.read_excel(RAW / "data_dictionary.xlsx", "Code Lists",
                          dtype=str).fillna("")
    out: dict[str, dict[str, str]] = {}
    for r in codes.itertuples(index=False):
        out.setdefault(r[0], {})[r[1]] = r[3]
    return out


def decode(s: pd.Series, field: str, lists: dict) -> pd.Series:
    """Map template codes to model values; stop on an unknown code."""
    unknown = set(s.unique()) - set(lists[field])
    if unknown:
        sys.exit(f"{field}: codes not in the data dictionary: {unknown}")
    return s.map(lists[field])


def number(s: pd.Series, field: str, allow_nd: bool = False) -> pd.Series:
    """Convert a template column to numbers, checking no-data codes."""
    is_nd = s.isin(ND)
    if is_nd.any() and not allow_nd:
        sys.exit(f"{field}: {is_nd.sum()} no-data codes in a required field")
    return pd.to_numeric(s.where(~is_nd), errors="raise")


def months_between(a: pd.Series, b: pd.Series) -> pd.Series:
    """Whole months from date a to date b."""
    pa = pd.to_datetime(a).dt.to_period("M")
    pb = pd.to_datetime(b).dt.to_period("M")
    return (pb - pa).apply(lambda x: x.n)


# --------------------------------------------------------------- UK RMBS
def prepare_rmbs_loans(lists) -> pd.DataFrame:
    folder = RAW / "uk_rmbs"
    # the FCA XML report: one record per loan, with its property
    df = fca_xml.read_report(folder / "THAMESBRIDGE_RRE_2019-12-31.zip",
                             "RRE")
    extra = read_report(folder / "Thamesbridge_originator_additional_data"
                        "_2019-12-31.xlsx")
    problems = fca_xml.check_rules(df, "RRE")
    if problems:
        sys.exit("FCA validation rules: " + "; ".join(problems))
    assert df["RREL3"].is_unique, "duplicate loan identifiers"
    assert (df["RREL3"] == df["RREC2"]).all(), "property not on its loan"
    df = df.merge(extra, left_on="RREL3", right_on="Loan Identifier",
                  how="left", validate="one_to_one")
    cutoff = df["RREL6"].iloc[0]
    seasoning = number(df["RREL58"], "RREL58").astype(int)
    check = months_between(df["RREL23"], pd.Series(cutoff, df.index))
    assert (check == seasoning).all(), "RREL58 disagrees with the dates"
    orig_bal = number(df["RREL29"], "RREL29")
    income = number(df["RREL16"], "RREL16")
    term = number(df["RREL25"], "RREL25").astype(int)
    loans = pd.DataFrame({
        "loan_id": df["RREL3"],
        "origination_date": df["RREL23"],
        "original_balance": orig_bal,
        "current_balance": number(df["RREL30"], "RREL30"),
        "property_value": number(df["RREC17"], "RREC17"),
        "original_ltv": number(df["RREC16"], "RREC16"),
        "current_ltv": number(df["RREC12"], "RREC12"),
        "interest_rate": number(df["RREL43"], "RREL43"),
        "fixed_rate_years": months_between(df["RREL23"], df["RREL51"]) // 12,
        "product_end_date": df["RREL51"],
        "term_months": term,
        "remaining_term_months": term - seasoning,
        "seasoning_months": seasoning,
        "repayment_type": decode(df["RREL35"], "RREL35", lists),
        "occupancy": decode(df["RREC7"], "RREC7", lists),
        "property_type": decode(df["RREC9"], "RREC9", lists),
        "region": decode(df["RREL11"].str[:3], "NUTS1", lists),
        "employment": decode(df["RREL13"], "RREL13", lists),
        "income": income,
        "loan_to_income": (orig_bal / income).round(2),
        "credit_score": df["Bureau Score at Origination"].astype(int),
    })
    return loans


TAPE_STATUS = {("LIVE", 0): "C", ("LIVE", 1): "30", ("LIVE", 2): "60",
               ("LIVE", 3): "90", ("REDEEMED", 0): "PRE"}


def prepare_performance() -> pd.DataFrame:
    tapes = sorted((RAW / "uk_rmbs" / "servicer_monthly").glob("*.xlsx"))
    frames = []
    for path in tapes:
        t = read_report(path)
        months = t["Months in Arrears"].fillna(-1).astype(int)
        status = [TAPE_STATUS.get((s, m), "DEF" if s == "DEFAULTED" else None)
                  for s, m in zip(t["Account Status"], months)]
        if None in status:
            sys.exit(f"{path.name}: unknown status combination")
        frames.append(pd.DataFrame({
            "loan_id": t["Loan Number"],
            "period": pd.to_datetime(t["Reporting Date"]).dt.strftime("%Y-%m"),
            "status": status,
            "opening_balance": t["Opening Balance"],
            "scheduled_payment": t["Scheduled Instalment"],
            "principal_paid": t["Scheduled Principal Received"],
            "interest_due": t["Interest Due"],
            "prepayment": t["Redemption Amount"],
            "default_balance": t["Balance Transferred to Default"],
            "closing_balance": t["Closing Balance"],
        }))
    perf = pd.concat(frames, ignore_index=True)
    # the balances of each tape must roll forward
    roll = (perf["opening_balance"] - perf["principal_paid"]
            - perf["prepayment"] - perf["default_balance"]
            - perf["closing_balance"]).abs()
    assert (roll < 0.02).all(), "balances do not roll forward"
    return perf


def reconcile_investor_report(perf: pd.DataFrame) -> None:
    """Arrears buckets of the last tape against the investor report."""
    ivss = read_report(RAW / "uk_rmbs" /
                       "Thamesbridge_investor_report_2024-12.xlsx")
    rep = dict(zip(ivss["Field Code"], ivss["Value"]))
    last = perf[perf["period"] == "2024-12"]
    live = last[last["status"].isin(["C", "30", "60", "90"])]
    pool = live["closing_balance"].sum()
    for field, status in [("IVSS39", "30"), ("IVSS40", "60"),
                          ("IVSS41", "90")]:
        tape = 100 * live.loc[live["status"] == status,
                              "closing_balance"].sum() / pool
        assert abs(tape - float(rep[field])) < 1e-3, f"{field} differs"


def prepare_defaults() -> pd.DataFrame:
    d = read_report(RAW / "uk_rmbs" /
                    "Thamesbridge_losses_and_recoveries_2024-12.xlsx")
    d["Default Date"] = pd.to_datetime(d["Default Date"]).dt.strftime("%Y-%m")
    d.columns = ["loan_id", "default_period", "months_since_origination",
                 "balance_at_default", "indexed_value_at_default",
                 "indexed_ltv_at_default", "recovery_lag_months",
                 "forced_sale_discount", "sale_value", "sale_costs",
                 "accrued_interest", "exposure_at_default", "recovery",
                 "loss", "loss_severity"]
    return d


def prepare_deal() -> dict:
    path = RAW / "uk_rmbs" / "Thamesbridge_deal_summary.xlsx"
    items = pd.read_excel(path, "Transaction")
    notes = pd.read_excel(path, "Notes")
    deal = {k: (v.item() if hasattr(v, "item") else v)
            for k, v in zip(items["Item"], items["Value"])}
    note = deal.pop("note")
    deal["tranches"] = [
        {"class": r["Class"], "share_of_pool": r["Share of Pool"],
         "balance": r["Original Balance (GBP)"],
         "margin_pct": (None if pd.isna(r["Margin over SONIA (%)"])
                        else r["Margin over SONIA (%)"]),
         "target_rating_illustrative": r["Rating (illustrative)"]}
        for _, r in notes.iterrows()]
    deal["note"] = note
    return deal


# --------------------------------------------------------------- economic
def prepare_macro() -> pd.DataFrame:
    eco = RAW / "economic"
    boe = pd.read_csv(eco / "BoE_IUMASOIA_monthly_average_SONIA.csv")
    boe["period"] = pd.to_datetime(boe["DATE"], format="%d %b %Y"
                                   ).dt.strftime("%Y-%m")
    ons = pd.read_csv(eco / "ONS_MGSX_unemployment_rate.csv", header=None,
                      names=["label", "value"])
    ons = ons[ons["label"].str.match(r"^\d{4} [A-Z]{3}$")]   # monthly rows
    ons["period"] = pd.to_datetime(ons["label"], format="%Y %b"
                                   ).dt.strftime("%Y-%m")
    hpi = pd.read_csv(eco / "UK-HPI-full-file-2024-12.csv")
    hpi = hpi[hpi["RegionName"] == "United Kingdom"].copy()
    hpi["period"] = pd.to_datetime(hpi["Date"], format="%d/%m/%Y"
                                   ).dt.strftime("%Y-%m")
    cci = pd.read_csv(eco / "internal_credit_cycle_index.csv")
    macro = (ons[["period", "value"]].astype({"value": float})
             .rename(columns={"value": "unemployment_rate"})
             .merge(hpi[["period", "Index"]], on="period", validate="1:1")
             .merge(boe[["period", "IUMASOIA"]], on="period", validate="1:1")
             .merge(cci, left_on="period", right_on="Month", validate="1:1"))
    return pd.DataFrame({"period": macro["period"],
                         "unemployment_rate": macro["unemployment_rate"],
                         "hpi": macro["Index"], "sonia": macro["IUMASOIA"],
                         "credit_factor": macro["Credit Cycle Index"]})


# --------------------------------------------------------------- auto
def prepare_auto(lists) -> pd.DataFrame:
    folder = RAW / "uk_auto"
    a = fca_xml.read_report(folder / "WESSEX_AUTO_2024-12-31.zip", "AUT")
    problems = fca_xml.check_rules(a, "AUT")
    if problems:
        sys.exit("FCA validation rules: " + "; ".join(problems))
    extra = read_report(folder / "Wessex_originator_additional_data"
                        "_2024-12-31.xlsx")
    a = a.merge(extra, left_on="AUTL3", right_on="Agreement Number",
                how="left", validate="one_to_one")
    outcome = decode(a["AUTL70"], "AUTL70", lists)
    # redeemed without a prepayment date: repaid at maturity, censored
    at_maturity = (a["AUTL70"] == "RDMD") & a["AUTL51"].isin(ND)
    outcome = outcome.where(~at_maturity, "censored")
    end = a["AUTL6"].where(outcome == "censored",
                           a["AUTL73"].where(outcome == "default",
                                             a["AUTL51"]))
    amount = number(a["AUTL29"], "AUTL29")
    deposit = number(a["AUTL39"], "AUTL39")
    value = number(a["AUTL60"], "AUTL60")
    default_amt = number(a["AUTL72"], "AUTL72", allow_nd=True)
    recovered = number(a["AUTL76"], "AUTL76", allow_nd=True)
    return pd.DataFrame({
        "loan_id": a["AUTL3"],
        "product": decode(a["AUTL23"], "AUTL23", lists),
        "vehicle": decode(a["AUTL56"], "AUTL56", lists),
        "credit_score": a["Bureau Score at Origination"].astype(int),
        "amount_financed": amount,
        "term_months": number(a["AUTL26"], "AUTL26").astype(int),
        "deposit_pct": (100 * deposit / value).round(1),
        "apr": number(a["AUTL40"], "AUTL40"),
        "months_observed": months_between(a["AUTL24"], end),
        "outcome": outcome,
        "default": (outcome == "default").astype(int),
        "recovery_rate_if_default": (recovered / default_amt).round(3),
    })


# --------------------------------------------------------------- CMBS, CLO
def prepare_cmbs() -> pd.DataFrame:
    c = read_report(RAW / "cmbs" / "CMBS_servicer_loan_history_2024-12.xlsx")
    for col in ["Term Default (Y/N)", "Maturity Default (Y/N)"]:
        c[col] = c[col].map({"Y": 1, "N": 0})
    c["Loss Severity (%)"] = (c["Loss Severity (%)"] / 100).round(4)
    c.columns = ["loan_id", "property_type", "property_value",
                 "loan_balance", "ltv", "interest_rate", "noi", "dscr",
                 "term_years", "noi_after_stress_period", "value_at_maturity",
                 "ltv_at_maturity", "term_default", "maturity_default",
                 "loss_severity"]
    money = ["property_value", "loan_balance", "noi",
             "noi_after_stress_period", "value_at_maturity"]
    c[money] = c[money].astype(float)        # amounts in pounds and pence
    return c


def prepare_assumptions() -> tuple[pd.DataFrame, pd.DataFrame]:
    path = RAW / "assumptions" / "rating_assumptions.xlsx"
    wide = read_report(path, "Default Table").set_index("Rating")
    long = wide.stack().reset_index()
    long.columns = ["rating", "horizon_years", "cumulative_pd"]
    long["horizon_years"] = long["horizon_years"].str.replace(
        "Year ", "").astype(int)
    stresses = pd.read_excel(path, "Rating Stresses")
    stresses.columns = ["rating", "default_multiple",
                        "market_value_decline_pct", "prepayment_stress",
                        "target_loss_quantile", "note"]
    return long, stresses


def prepare_clo(table: pd.DataFrame) -> pd.DataFrame:
    c = read_report(RAW / "clo" / "CLO_trustee_report_2024-12.xlsx")
    pd1 = table[table["horizon_years"] == 1].set_index("rating")
    report_year = 2024
    return pd.DataFrame({
        "obligor": c["Obligor Name"],
        "industry": c["Industry Classification"],
        "rating": c["Rating (illustrative)"],
        "par": c["Par Amount (EUR)"].astype(float),
        "spread_pct": c["Spread (%)"],
        "years_to_maturity": pd.to_datetime(c["Maturity Date"]).dt.year
        - report_year,
        "recovery_assumption": (c["Recovery Rate Assumption (%)"] / 100
                                ).round(2),
        "one_year_pd": c["Rating (illustrative)"].map(pd1["cumulative_pd"]),
    })


def main() -> None:
    lists = code_lists()
    loans = prepare_rmbs_loans(lists)
    perf = prepare_performance()
    reconcile_investor_report(perf)
    table, stresses = prepare_assumptions()
    outputs = {
        "macro.csv": prepare_macro(),
        "rmbs_loans.csv": loans,
        "rmbs_defaults.csv": prepare_defaults(),
        "cmbs_loans.csv": prepare_cmbs(),
        "auto_loans.csv": prepare_auto(lists),
        "clo_portfolio.csv": prepare_clo(table),
        "rating_default_table.csv": table,
        "rating_stresses.csv": stresses,
    }
    for name, df in outputs.items():
        df.to_csv(OUT / name, index=False)
    perf.to_csv(OUT / "rmbs_performance.csv.gz", index=False,
                compression={"method": "gzip", "mtime": 0})
    (OUT / "rmbs_deal.json").write_text(json.dumps(prepare_deal(), indent=2))
    print(f"{len(loans):,} loans, {len(perf):,} performance rows, "
          f"{len(outputs) + 2} tables written to data/")


if __name__ == "__main__":
    main()
