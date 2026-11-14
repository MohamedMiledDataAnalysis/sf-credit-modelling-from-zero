"""Write the synthetic datasets in the formats of real work.

Called by generate_data.py. Every file in data/raw/ is produced here:
regulatory loan-level templates (CSV, one header row of field codes),
servicer and trustee Excel reports with their title blocks, public
economic data in the layout of the real downloads, and the data
dictionary. scripts/prepare_data.py turns them into the model tables.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

import fca_xml
import templates as T

LEI = "FICTTHAMESBRIDGE0001"          # fictional, 20 characters
AUTO_LEI = "FICTWESSEXMOTOR00001"
UID_RMBS = LEI + "N" + "2020" + "01"   # LEI + N + year + sequence
UID_AUTO = AUTO_LEI + "N" + "2023" + "01"
NAVY = "1F2A44"


def _title_block(ws, lines):
    for i, line in enumerate(lines, 1):
        ws.append(line)
        if i == 1:
            ws.cell(1, 1).font = Font(bold=True, size=13)
    ws.append([])


def _header(ws, row_idx, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row_idx, c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=NAVY)


def _report(path, title_lines, df, sheet="Report"):
    """An Excel report: title block, blank row, table."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    _title_block(ws, title_lines)
    ws.append(list(df.columns))
    hdr = len(title_lines) + 2
    _header(ws, hdr, df.shape[1])
    for row in df.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and np.isnan(v)) else v
                   for v in row])
    ws.freeze_panes = ws.cell(hdr + 1, 1)
    wb.save(path)


def _as_text(df: pd.DataFrame) -> pd.DataFrame:
    """Every value as the text a CSV export would hold."""
    return pd.read_csv(io.StringIO(df.to_csv(index=False)), dtype=str,
                       keep_default_na=False)


def _month_end(period: str) -> str:
    return pd.Period(period, "M").to_timestamp(how="end").strftime("%Y-%m-%d")


# ---------------------------------------------------------------- RMBS
def rmbs_loan_level(loans: pd.DataFrame, out: Path, rng) -> None:
    n = len(loans)
    nd5 = ["ND5"] * n
    orig = pd.to_datetime(loans["origination_date"])
    maturity = (orig.dt.to_period("M") + loans["term_months"]).dt.to_timestamp()
    rate = loans["interest_rate"] / 100 / 12
    rem = loans["remaining_term_months"]
    annuity = loans["current_balance"] * rate / (1 - (1 + rate) ** (-rem))
    io = loans["repayment_type"] == "Interest-only"
    payment = np.where(io, loans["current_balance"] * rate, annuity).round(2)
    nuts3 = loans["region"].map(T.NUTS3_EXAMPLE)
    lender = "Thamesbridge Building Society"
    v = {
        "RREL1": [UID_RMBS] * n, "RREL2": loans["loan_id"],
        "RREL3": loans["loan_id"],
        "RREL4": ["OB" + s[2:] for s in loans["loan_id"]],
        "RREL5": ["OB" + s[2:] for s in loans["loan_id"]],
        "RREL6": ["2019-12-31"] * n, "RREL7": ["2019-12-31"] * n,
        "RREL8": nd5, "RREL9": nd5, "RREL10": ["Y"] * n,
        "RREL11": nuts3, "RREL12": [2016] * n,
        "RREL13": np.where(loans["employment"] == "Employed", "EMUK", "SFEM"),
        "RREL14": ["N"] * n,
        "RREL15": rng.choice(["CNEO", "ENEO"], n, p=[0.8, 0.2]),
        "RREL16": loans["income"], "RREL17": ["ND1"] * n,
        "RREL18": ["GBP"] * n, "RREL19": ["ND1"] * n,
        "RREL20": ["ND1"] * n, "RREL21": ["ND1"] * n, "RREL22": nd5,
        "RREL23": loans["origination_date"],
        "RREL24": maturity.dt.strftime("%Y-%m-%d"),
        "RREL25": loans["term_months"],
        "RREL26": rng.choice(["BROK", "BRAN", "WEBI"], n, p=[0.7, 0.2, 0.1]),
        "RREL27": rng.choice(["PURC", "RMRT"], n, p=[0.6, 0.4]),
        "RREL28": ["GBP"] * n, "RREL29": loans["original_balance"],
        "RREL30": loans["current_balance"], "RREL31": [0] * n,
        "RREL32": [0] * n, "RREL33": nd5, "RREL34": [100] * n,
        "RREL35": np.where(io, "BLLT", "FRXX"), "RREL36": nd5,
        "RREL37": ["MNTH"] * n, "RREL38": ["MNTH"] * n,
        "RREL39": payment, "RREL40": ["ND1"] * n,
        "RREL41": np.where(io, loans["current_balance"], 0),
        "RREL42": ["FLCF"] * n, "RREL43": loans["interest_rate"],
        "RREL44": nd5, "RREL45": nd5, "RREL46": nd5, "RREL47": nd5,
        "RREL48": nd5, "RREL49": nd5, "RREL50": [3.75] * n,
        "RREL51": loans["product_end_date"], "RREL52": nd5,
        "RREL53": nd5, "RREL54": nd5, "RREL55": nd5,
        "RREL56": ["BOER"] * n, "RREL57": nd5,
        "RREL58": loans["seasoning_months"], "RREL59": [10] * n,
        "RREL60": nd5, "RREL61": nd5,
        "RREL62": loans["product_end_date"], "RREL63": nd5,
        "RREL64": [0] * n, "RREL65": nd5, "RREL66": nd5,
        "RREL67": [0] * n, "RREL68": [0] * n, "RREL69": ["PERF"] * n,
        "RREL70": nd5, "RREL71": nd5, "RREL72": nd5, "RREL73": [0] * n,
        "RREL74": nd5, "RREL75": ["N"] * n, "RREL76": ["Y"] * n,
        "RREL77": [0] * n, "RREL78": nd5,
        "RREL79": [lender] * n, "RREL80": [LEI] * n, "RREL81": ["GB"] * n,
        "RREL82": [lender] * n, "RREL83": [LEI] * n, "RREL84": ["GB"] * n,
    }
    rrel = pd.DataFrame(v)[[c for c, _, _ in T.fields(T.RREL)]]

    occ = loans["occupancy"].map({"Owner-occupied": "FOWN",
                                  "Buy-to-let": "TLET"})
    ptype = loans["property_type"].map({"House": "RHOS", "Flat": "RFLT",
                                        "Bungalow": "RBGL"})
    c = {
        "RREC1": [UID_RMBS] * n, "RREC2": loans["loan_id"],
        "RREC3": ["PR" + s[2:] for s in loans["loan_id"]],
        "RREC4": ["PR" + s[2:] for s in loans["loan_id"]],
        "RREC5": ["RBLD"] * n, "RREC6": nuts3, "RREC7": occ,
        "RREC8": [1] * n, "RREC9": ptype, "RREC10": ["ND1"] * n,
        "RREC11": ["ND1"] * n, "RREC12": loans["current_ltv"],
        "RREC13": loans["property_value"], "RREC14": ["FIEI"] * n,
        "RREC15": loans["origination_date"],
        "RREC16": loans["original_ltv"],
        "RREC17": loans["property_value"], "RREC18": ["FIEI"] * n,
        "RREC19": loans["origination_date"], "RREC20": nd5,
        "RREC21": nd5, "RREC22": ["GBP"] * n, "RREC23": ["NGUA"] * n,
    }
    rrec = pd.DataFrame(c)[[c for c, _, _ in T.fields(T.RREC)]]
    table = _as_text(rrel).merge(_as_text(rrec), left_on="RREL3",
                                 right_on="RREC2")
    fca_xml.write_report(table, "RRE",
                         out / "THAMESBRIDGE_RRE_2019-12-31.zip")

    extra = pd.DataFrame({"Loan Identifier": loans["loan_id"],
                          "Bureau Score at Origination":
                          loans["credit_score"]})
    _report(out / "Thamesbridge_originator_additional_data_2019-12-31.xlsx",
            [["Thamesbridge Building Society"],
             ["Additional loan data supplied with the loan tape"],
             ["Data cut-off date", "2019-12-31"]], extra, "Additional data")


STATUS_TO_TAPE = {"C": ("LIVE", 0), "30": ("LIVE", 1), "60": ("LIVE", 2),
                  "90": ("LIVE", 3), "DEF": ("DEFAULTED", None),
                  "PRE": ("REDEEMED", 0)}


def servicer_tapes(perf: pd.DataFrame, out: Path) -> None:
    folder = out / "servicer_monthly"
    folder.mkdir(exist_ok=True)
    cols = ["Loan Number", "Reporting Date", "Account Status",
            "Months in Arrears", "Opening Balance", "Scheduled Instalment",
            "Scheduled Principal Received", "Interest Due",
            "Redemption Amount", "Balance Transferred to Default",
            "Closing Balance"]
    for period, g in perf.groupby("period", sort=True):
        wb = Workbook(write_only=True)
        ws = wb.create_sheet("Loan Level")
        ws.append(["Thamesbridge Mortgages No. 1 plc"])
        ws.append(["Monthly loan-level servicer report"])
        ws.append(["Reporting date", _month_end(period)])
        ws.append([])
        ws.append(cols)
        date = _month_end(period)
        for r in g.itertuples(index=False):
            st, months = STATUS_TO_TAPE[r.status]
            ws.append([r.loan_id, date, st, months, r.opening_balance,
                       r.scheduled_payment, r.principal_paid, r.interest_due,
                       r.prepayment, r.default_balance, r.closing_balance])
        wb.save(folder / f"Thamesbridge_servicer_report_{period}.xlsx")


def losses_report(defaults: pd.DataFrame, out: Path) -> None:
    d = defaults.copy()
    d["default_period"] = d["default_period"].map(_month_end)
    d.columns = ["Loan Number", "Default Date", "Months Since Origination",
                 "Balance at Default", "Indexed Valuation at Default",
                 "Indexed LTV at Default (%)", "Months to Sale",
                 "Forced Sale Discount", "Sale Price", "Sale Costs",
                 "Accrued Interest", "Total Exposure at Default",
                 "Net Recovery", "Loss", "Loss Severity"]
    _report(out / "Thamesbridge_losses_and_recoveries_2024-12.xlsx",
            [["Thamesbridge Mortgages No. 1 plc"],
             ["Defaults, possessions and recoveries report"],
             ["Reporting date", "2024-12-31"]], d, "Losses")


def investor_report(perf, defaults, deal, out: Path) -> None:
    p = perf[perf["period"] == "2024-12"]
    live = p[p["status"].isin(["C", "30", "60", "90"])]
    pool = live["closing_balance"].sum()

    def bucket(s):
        return round(100 * live.loc[live["status"] == s,
                                    "closing_balance"].sum() / pool, 4)

    smm = p["prepayment"].sum() / p["opening_balance"].sum()
    mdr = p["default_balance"].sum() / p["opening_balance"].sum()
    rec = defaults[(pd.PeriodIndex(defaults["default_period"], freq="M")
                    + defaults["recovery_lag_months"]).astype(str)
                   == "2024-12"]["recovery"].sum()
    princ = (p["principal_paid"] + p["prepayment"]).sum()
    intr = p.loc[p["status"] == "C", "interest_due"].sum()
    cum_def = perf["default_balance"].sum()
    vals = {
        "IVSS1": UID_RMBS, "IVSS2": "2024-12-31",
        "IVSS3": deal["deal_name"],
        "IVSS4": "Thamesbridge Building Society",
        "IVSS5": "Investor Reporting Team",
        "IVSS6": "+44 20 7946 0000",
        "IVSS7": "investor.reporting@thamesbridge.example",
        "IVSS8": "VSLC", "IVSS9": "ORIG", "IVSS10": "RMRT",
        "IVSS11": "Y", "IVSS12": "N", "IVSS13": "ND5",
        "IVSS14": round(rec, 2), "IVSS15": 0,
        "IVSS16": round(princ, 2), "IVSS17": round(intr, 2),
        "IVSS18": "N", "IVSS19": "ND5", "IVSS20": "Y", "IVSS21": "ND5",
        "IVSS22": round(100 * (1 - (1 - smm) ** 12), 4),
        "IVSS23": 0, "IVSS24": round(p["default_balance"].sum(), 2),
        "IVSS25": 0, "IVSS26": 0,
        "IVSS27": round(100 * (1 - (1 - mdr) ** 12), 4),
        "IVSS28": round(cum_def, 2), "IVSS29": "ND5", "IVSS30": "ND5",
        "IVSS31": "ND5", "IVSS32": "ND5", "IVSS33": "ND5",
        "IVSS34": "ND5", "IVSS35": "ND5", "IVSS36": "ND5",
        "IVSS37": "ND5", "IVSS38": 0, "IVSS39": bucket("30"),
        "IVSS40": bucket("60"), "IVSS41": bucket("90"), "IVSS42": 0,
        "IVSS43": 0, "IVSS44": 0,
    }
    wb = Workbook()
    ws = wb.active
    ws.title = "IVSS Securitisation"
    rows = [(c, n, f, vals[c]) for c, n, f in T.fields(T.IVSS)]
    _title_block(ws, [[deal["deal_name"]],
                      ["Investor report - Annex 12 securitisation section"],
                      ["Data cut-off date", "2024-12-31"]])
    ws.append(["Field Code", "Field Name", "Format", "Value"])
    _header(ws, 5, 4)
    for r in rows:
        ws.append(list(r))
    cum_pct = round(100 * cum_def / deal["pool_balance"], 4)
    ws2 = wb.create_sheet("IVSR Tests-Triggers")
    ws2.append([c for c, _, _ in T.fields(T.IVSR)])
    ws2.append([n for _, n, _ in T.fields(T.IVSR)])
    ws2.append([UID_RMBS, "TRIG01", "TRIG01",
                "Cumulative defaults as a percentage of the pool balance "
                "at closing", 3.0, cum_pct, "Y" if cum_pct < 3 else "N",
                0, 1, "OTHR"])
    ws3 = wb.create_sheet("IVSF Cash Flows")
    ws3.append([c for c, _, _ in T.fields(T.IVSF)])
    ws3.append([n for _, n, _ in T.fields(T.IVSF)])
    ws3.append([UID_RMBS, "CF01", "CF01", "Interest collections",
                round(intr, 2), round(intr, 2)])
    ws3.append([UID_RMBS, "CF02", "CF02", "Principal collections",
                round(princ, 2), round(intr + princ, 2)])
    wb.save(out / "Thamesbridge_investor_report_2024-12.xlsx")


def deal_summary(deal: dict, out: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Transaction"
    ws.append(["Item", "Value"])
    _header(ws, 1, 2)
    for k, v in deal.items():
        if k != "tranches":
            ws.append([k, v])
    ws2 = wb.create_sheet("Notes")
    ws2.append(["Class", "Share of Pool", "Original Balance (GBP)",
                "Margin over SONIA (%)", "Rating (illustrative)"])
    _header(ws2, 1, 5)
    for t in deal["tranches"]:
        ws2.append([t["class"], t["share_of_pool"], t["balance"],
                    t["margin_pct"], t["target_rating_illustrative"]])
    wb.save(out / "Thamesbridge_deal_summary.xlsx")


# ---------------------------------------------------------------- macro
def economic(macro: pd.DataFrame, out: Path) -> None:
    ends = [_month_end(p) for p in macro["period"]]
    # Bank of England Database CSV export: DATE, series code
    boe = pd.DataFrame({
        "DATE": [pd.Timestamp(d).strftime("%d %b %Y") for d in ends],
        "IUMASOIA": macro["sonia"]})
    boe.to_csv(out / "BoE_IUMASOIA_monthly_average_SONIA.csv", index=False)
    # ONS time series CSV: metadata rows, then "YYYY MON" rows
    with open(out / "ONS_MGSX_unemployment_rate.csv", "w",
              newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["Title", "Unemployment rate (aged 16 and over, "
                    "seasonally adjusted): % (synthetic values for "
                    "the book)"])
        w.writerow(["CDID", "MGSX"])
        w.writerow(["Source dataset ID", "LMS"])
        w.writerow(["PreUnit", ""])
        w.writerow(["Unit", "%"])
        w.writerow(["Release date", "21-01-2025"])
        w.writerow(["Next release", "18 February 2025"])
        w.writerow(["Important notes", "Synthetic series for teaching"])
        for p, u in zip(macro["period"], macro["unemployment_rate"]):
            per = pd.Period(p, "M")
            w.writerow([f"{per.year} {per.strftime('%b').upper()}",
                        repr(float(u))])
    # HM Land Registry UK House Price Index full file (first columns)
    idx = macro["hpi"]
    hpi = pd.DataFrame({
        "Date": [pd.Period(p, "M").to_timestamp().strftime("%d/%m/%Y")
                 for p in macro["period"]],
        "RegionName": "United Kingdom", "AreaCode": "K02000001",
        "AveragePrice": (idx * 1900).round(0).astype(int),
        "Index": idx, "IndexSA": idx,
        "1m%Change": (idx.pct_change() * 100).round(1),
        "12m%Change": (idx.pct_change(12) * 100).round(1),
        "AveragePriceSA": (idx * 1900).round(0).astype(int),
        "SalesVolume": "",
    })
    hpi.to_csv(out / "UK-HPI-full-file-2024-12.csv", index=False)
    pd.DataFrame({"Month": macro["period"],
                  "Credit Cycle Index": macro["credit_factor"]}).to_csv(
        out / "internal_credit_cycle_index.csv", index=False)


# ---------------------------------------------------------------- auto
def auto_loan_level(auto: pd.DataFrame, out: Path, rng) -> None:
    n = len(auto)
    nd5 = ["ND5"] * n
    cutoff = pd.Period("2024-12", "M")
    gap = np.where(auto["outcome"] == "censored", 0,
                   rng.integers(1, 13, n))
    end = [cutoff - int(g) for g in gap]
    start = [e - int(m) for e, m in zip(end, auto["months_observed"])]
    day15 = lambda p: p.to_timestamp().strftime("%Y-%m-15")  # noqa: E731
    orig = [day15(p) for p in start]
    event = [day15(p) for p in end]
    mat = [day15(p + int(t)) for p, t in zip(start, auto["term_months"])]
    val = (auto["amount_financed"] / (1 - auto["deposit_pct"] / 100)).round(2)
    dep = (val - auto["amount_financed"]).round(2)
    pre = auto["outcome"] == "prepaid"
    dft = auto["outcome"] == "default"
    frac = 1 - auto["months_observed"] / auto["term_months"]
    def_amt = (auto["amount_financed"] * frac.clip(0.05, 1)).round(2)
    rec = (def_amt * auto["recovery_rate_if_default"]).round(2)
    status = auto["outcome"].map({"censored": "PERF", "prepaid": "RDMD",
                                  "default": "DFLT"})
    lender = "Wessex Motor Finance Limited"
    v = {c: nd5 for c, _, _ in T.fields(T.AUTL)}
    v.update({
        "AUTL1": [UID_AUTO] * n, "AUTL2": auto["loan_id"],
        "AUTL3": auto["loan_id"],
        "AUTL4": ["CU" + s[2:] for s in auto["loan_id"]],
        "AUTL5": ["CU" + s[2:] for s in auto["loan_id"]],
        "AUTL6": ["2024-12-31"] * n, "AUTL7": ["2023-06-30"] * n,
        "AUTL9": np.where(pre, event, "ND5"),
        "AUTL10": ["ND1"] * n, "AUTL11": [2016] * n,
        "AUTL12": ["ND1"] * n, "AUTL13": ["N"] * n,
        "AUTL14": ["INDV"] * n, "AUTL15": ["ND1"] * n,
        "AUTL16": ["ND1"] * n, "AUTL17": ["ND1"] * n,
        "AUTL18": ["GBP"] * n, "AUTL19": ["ND1"] * n,
        "AUTL23": auto["product"].map({"PCP": "PPUR", "HP": "HIRP"}),
        "AUTL24": orig, "AUTL25": mat, "AUTL26": auto["term_months"],
        "AUTL27": ["ND1"] * n, "AUTL28": ["GBP"] * n,
        "AUTL29": auto["amount_financed"],
        "AUTL30": np.where(status == "PERF",
                           (auto["amount_financed"] * frac).round(2), 0),
        "AUTL31": [100] * n, "AUTL32": ["FRXX"] * n,
        "AUTL34": ["MNTH"] * n, "AUTL35": ["MNTH"] * n,
        "AUTL36": ["CDTX"] * n, "AUTL39": dep, "AUTL40": auto["apr"],
        "AUTL47": [max(0, (pd.Period("2023-06", "M") - p).n)
                   for p in start],
        "AUTL53": ["ND1"] * n, "AUTL54": ["ND1"] * n,
        "AUTL51": np.where(pre, event, "ND5"),
        "AUTL52": np.where(pre, auto["amount_financed"], 0),
        "AUTL56": auto["vehicle"].map({"New": "NEWX", "Used": "USED"}),
        "AUTL59": (100 * auto["amount_financed"] / val).round(2),
        "AUTL60": val, "AUTL68": [0] * n, "AUTL69": [0] * n,
        "AUTL70": status, "AUTL71": np.where(dft, "PDXX", "ND5"),
        "AUTL72": np.where(dft, def_amt, "ND5"),
        "AUTL73": np.where(dft, event, "ND5"),
        "AUTL74": np.where(dft, (def_amt - rec).round(2), 0),
        "AUTL76": np.where(dft, rec, "ND5"), "AUTL78": dep,
        "AUTL79": [lender] * n, "AUTL80": [AUTO_LEI] * n,
        "AUTL81": ["GB"] * n, "AUTL82": [lender] * n,
        "AUTL83": [AUTO_LEI] * n, "AUTL84": ["GB"] * n,
    })
    autl = pd.DataFrame(v)[[c for c, _, _ in T.fields(T.AUTL)]]
    fca_xml.write_report(_as_text(autl), "AUT",
                         out / "WESSEX_AUTO_2024-12-31.zip")
    extra = pd.DataFrame({"Agreement Number": auto["loan_id"],
                          "Bureau Score at Origination": auto["credit_score"]})
    _report(out / "Wessex_originator_additional_data_2024-12-31.xlsx",
            [["Wessex Motor Finance Limited"],
             ["Additional loan data supplied with the loan tape"],
             ["Data cut-off date", "2024-12-31"]], extra, "Additional data")


# ---------------------------------------------------------------- CMBS, CLO
def cmbs_report(cmbs: pd.DataFrame, out: Path) -> None:
    d = cmbs.copy()
    for c in ["term_default", "maturity_default"]:
        d[c] = d[c].map({1: "Y", 0: "N"})
    d["loss_severity"] = (d["loss_severity"] * 100).round(2)
    d.columns = ["Loan ID", "Property Type", "Valuation at Origination (GBP)",
                 "Loan Balance (GBP)", "LTV (%)", "Interest Rate (%)",
                 "NOI at Origination (GBP)", "DSCR (x)",
                 "Loan Term (Years)", "NOI at Maturity (GBP)",
                 "Valuation at Maturity (GBP)", "LTV at Maturity (%)",
                 "Term Default (Y/N)", "Maturity Default (Y/N)",
                 "Loss Severity (%)"]
    _report(out / "CMBS_servicer_loan_history_2024-12.xlsx",
            [["UK CMBS loan history - 2010 to 2024 vintages (synthetic)"],
             ["Special servicer loan-level history report"],
             ["Reporting date", "2024-12-31"]], d, "Loan History")


def clo_report(clo: pd.DataFrame, out: Path) -> None:
    d = pd.DataFrame({
        "Obligor Name": clo["obligor"],
        "Industry Classification": clo["industry"],
        "Rating (illustrative)": clo["rating"],
        "Par Amount (EUR)": clo["par"], "Spread (%)": clo["spread_pct"],
        "Maturity Date": [f"{2024 + int(y)}-12-31"
                          for y in clo["years_to_maturity"]],
        "Recovery Rate Assumption (%)":
            (clo["recovery_assumption"] * 100).round(0).astype(int),
    })
    _report(out / "CLO_trustee_report_2024-12.xlsx",
            [["Avon Valley CLO I DAC (fictional)"],
             ["Monthly trustee report - collateral portfolio"],
             ["Determination date", "2024-12-31"]], d,
            "Collateral Portfolio")


def assumptions(table: pd.DataFrame, stresses: pd.DataFrame, out: Path):
    wide = table.pivot(index="rating", columns="horizon_years",
                       values="cumulative_pd")
    wide = wide.loc[table["rating"].unique()]
    wide.columns = [f"Year {h}" for h in wide.columns]
    wb = Workbook()
    ws = wb.active
    ws.title = "Default Table"
    _title_block(ws, [["Rating criteria assumptions (illustrative)"],
                      ["Cumulative default probability by rating and "
                       "horizon"], ["Version", "Book edition 1"]])
    ws.append(["Rating"] + list(wide.columns))
    _header(ws, 5, wide.shape[1] + 1)
    for r, row in wide.iterrows():
        ws.append([r] + list(row))
    ws2 = wb.create_sheet("Rating Stresses")
    ws2.append(["Rating", "Default Multiple", "Market Value Decline (%)",
                "Prepayment Stress", "Target Loss Quantile", "Note"])
    _header(ws2, 1, 6)
    for row in stresses.itertuples(index=False):
        ws2.append(list(row))
    wb.save(out / "rating_assumptions.xlsx")


# ---------------------------------------------------------------- dictionary
def dictionary(out: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Files"
    files = [
        ("uk_rmbs/THAMESBRIDGE_RRE_2019-12-31.zip", "RREL, RREC",
         "FCA underlying exposure report, zipped XML "
         "(DRAFT3auth.099.001.04), "
         "residential real estate: loan and collateral sections",
         "Cut-off"),
        ("uk_rmbs/Thamesbridge_originator_additional_data_2019-12-31.xlsx",
         "Additional", "Originator data outside the template", "Cut-off"),
        ("uk_rmbs/Thamesbridge_deal_summary.xlsx", "Deal",
         "Term sheet summary: transaction and notes", "Closing"),
        ("uk_rmbs/servicer_monthly/Thamesbridge_servicer_report_YYYY-MM"
         ".xlsx", "Servicer tape", "Monthly loan-level servicer report",
         "Monthly"),
        ("uk_rmbs/Thamesbridge_losses_and_recoveries_2024-12.xlsx",
         "Losses", "Defaults, possessions and recoveries", "Monthly"),
        ("uk_rmbs/Thamesbridge_investor_report_2024-12.xlsx", "IVSS",
         "Investor report (Annex 12)", "Monthly"),
        ("economic/BoE_IUMASOIA_monthly_average_SONIA.csv", "Economic",
         "Bank of England Database export", "Monthly"),
        ("economic/ONS_MGSX_unemployment_rate.csv", "Economic",
         "ONS time series download", "Monthly"),
        ("economic/UK-HPI-full-file-2024-12.csv", "Economic",
         "HM Land Registry UK HPI full file", "Monthly"),
        ("economic/internal_credit_cycle_index.csv", "Economic",
         "Internal credit cycle index (model input)", "Monthly"),
        ("uk_auto/WESSEX_AUTO_2024-12-31.zip", "AUTL",
         "FCA underlying exposure report, zipped XML "
         "(DRAFT3auth.099.001.04), "
         "automobile", "Cut-off"),
        ("uk_auto/Wessex_originator_additional_data_2024-12-31.xlsx",
         "Additional", "Originator data outside the template", "Cut-off"),
        ("cmbs/CMBS_servicer_loan_history_2024-12.xlsx", "CMBS",
         "Special servicer loan history", "Annual"),
        ("clo/CLO_trustee_report_2024-12.xlsx", "CLO",
         "Trustee report, collateral portfolio", "Monthly"),
        ("assumptions/rating_assumptions.xlsx", "Assumptions",
         "Rating criteria tables (illustrative)", "Per version"),
    ]
    ws.append(["File (under data/raw/)", "Dictionary sheet", "Content",
               "Frequency"])
    _header(ws, 1, 4)
    for f in files:
        ws.append(list(f))

    model = {
        "RREL3": "loan_id", "RREL11": "region", "RREL13": "employment",
        "RREL16": "income", "RREL23": "origination_date",
        "RREL25": "term_months", "RREL29": "original_balance",
        "RREL30": "current_balance", "RREL35": "repayment_type",
        "RREL43": "interest_rate", "RREL51": "product_end_date",
        "RREL58": "seasoning_months", "RREC7": "occupancy",
        "RREC9": "property_type", "RREC12": "current_ltv",
        "RREC16": "original_ltv", "RREC17": "property_value",
        "AUTL3": "loan_id", "AUTL23": "product", "AUTL26": "term_months",
        "AUTL29": "amount_financed", "AUTL39": "deposit_pct",
        "AUTL40": "apr", "AUTL56": "vehicle", "AUTL70": "outcome",
        "AUTL72": "recovery_rate_if_default",
        "AUTL76": "recovery_rate_if_default",
    }
    nd_rule = {"{LIST}": "Codes in sheet Code Lists"}
    xml = pd.read_csv(Path(fca_xml.PATHS), dtype=str,
                      keep_default_na=False).set_index("field")
    for name, block in [("RREL", T.RREL), ("RREC", T.RREC),
                        ("AUTL", T.AUTL), ("IVSS", T.IVSS)]:
        s = wb.create_sheet(name)
        s.append(["Field Code", "Field Name", "Format", "Allowed Values",
                  "No-Data Codes Allowed", "XML Path", "Model Column"])
        _header(s, 1, 7)
        for code, fname, fmt in T.fields(block):
            x = xml.loc[code] if code in xml.index else None
            s.append([code, fname, fmt, nd_rule.get(fmt, ""),
                      "" if x is None else x["nd_codes"],
                      "Ccy attribute of every amount" if x is None
                      and fmt == "{CURRENCYCODE_3}" else
                      ("" if x is None else x["value_path"]),
                      model.get(code, "")])

    bespoke = {
        "Additional": [("Loan Identifier / Agreement Number", "Text",
                        "loan_id"),
                       ("Bureau Score at Origination", "Integer",
                        "credit_score")],
        "Servicer tape": [
            ("Loan Number", "Text", "loan_id"),
            ("Reporting Date", "YYYY-MM-DD (month end)", "period"),
            ("Account Status", "LIVE / REDEEMED / DEFAULTED", "status"),
            ("Months in Arrears", "Integer 0-3, blank if defaulted",
             "status"),
            ("Opening Balance", "GBP", "opening_balance"),
            ("Scheduled Instalment", "GBP", "scheduled_payment"),
            ("Scheduled Principal Received", "GBP", "principal_paid"),
            ("Interest Due", "GBP", "interest_due"),
            ("Redemption Amount", "GBP", "prepayment"),
            ("Balance Transferred to Default", "GBP", "default_balance"),
            ("Closing Balance", "GBP", "closing_balance")],
        "Losses": [("Default Date", "YYYY-MM-DD (month end)",
                    "default_period"),
                   ("Other columns", "GBP, %, months or ratio",
                    "same order as rmbs_defaults.csv")],
        "Deal": [("Transaction sheet", "Item / Value", "rmbs_deal.json"),
                 ("Notes sheet", "One row per class", "tranches")],
        "Economic": [
            ("DATE / IUMASOIA", "DD Mon YYYY / % a year", "sonia"),
            ("ONS rows 'YYYY MON'", "% after 8 metadata rows",
             "unemployment_rate"),
            ("Index (RegionName = United Kingdom)", "Jan 2015 = 100",
             "hpi"),
            ("Credit Cycle Index", "Standardised factor",
             "credit_factor")],
        "CMBS": [("Term Default (Y/N), Maturity Default (Y/N)", "Y/N",
                  "term_default, maturity_default (1/0)"),
                 ("Loss Severity (%)", "Percentage", "loss_severity "
                  "(fraction)")],
        "CLO": [("Maturity Date", "YYYY-MM-DD", "years_to_maturity"),
                ("Recovery Rate Assumption (%)", "Percentage",
                 "recovery_assumption (fraction)"),
                ("Rating (illustrative)", "Rating scale",
                 "rating, one_year_pd via Default Table")],
        "Assumptions": [("Default Table", "Rating x Year 1-10",
                         "rating_default_table (long format)"),
                        ("Rating Stresses", "One row per rating",
                         "rating_stresses")],
    }
    for name, rows in bespoke.items():
        s = wb.create_sheet(name)
        s.append(["Field", "Format", "Model Column"])
        _header(s, 1, 3)
        for r in rows:
            s.append(list(r))

    s = wb.create_sheet("Code Lists")
    s.append(["Field Code", "Code", "Meaning", "Model Value"])
    _header(s, 1, 4)
    for r in T.CODE_LISTS:
        s.append(list(r))
    for k, v in T.NUTS1.items():
        s.append(["NUTS1", k, v, v])
    for k, v in T.ND_CODES.items():
        s.append(["ND", k, v, ""])
    wb.save(out / "data_dictionary.xlsx")


def write_all(raw: Path, rng, macro, loans, perf, defaults, deal, cmbs,
              auto, clo, table, stresses) -> None:
    dirs = {k: raw / k for k in ["uk_rmbs", "economic", "uk_auto", "cmbs",
                                 "clo", "assumptions"]}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    rmbs_loan_level(loans, dirs["uk_rmbs"], rng)
    servicer_tapes(perf, dirs["uk_rmbs"])
    losses_report(defaults, dirs["uk_rmbs"])
    investor_report(perf, defaults, deal, dirs["uk_rmbs"])
    deal_summary(deal, dirs["uk_rmbs"])
    economic(macro, dirs["economic"])
    auto_loan_level(auto, dirs["uk_auto"], rng)
    cmbs_report(cmbs, dirs["cmbs"])
    clo_report(clo, dirs["clo"])
    assumptions(table, stresses, dirs["assumptions"])
    dictionary(raw)
