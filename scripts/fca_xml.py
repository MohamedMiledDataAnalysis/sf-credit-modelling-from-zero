"""Write and read the FCA underlying exposure report (XML).

UK securitisations make their loan-level data available to a
securitisation repository as XML, in the FCA message
DRAFT3auth.099.001.04 (XML schemas and validation rules v1.3.2,
published on the FCA securitisation page). Each template field code
(RREL69, AUTL70, ...) sits at a fixed path in that message;
fca_xml_paths.csv lists the path of every field used here, taken from
the FCA validation rules workbook.

    write_report(table, "RRE", "file.zip")   # field-code table -> XML
    read_report("file.zip", "RRE")           # XML -> field-code table

The table has one column per field code and holds text, including the
no-data codes ND1-ND5, exactly as in the template.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
from lxml import etree

NS = "urn:fca:xsd:DRAFT3auth.099.001.04"
MESSAGE = "ScrtstnNonAsstBckdComrclPprUndrlygXpsrRpt"
RECORD = "UndrlygXpsrRcrd"
PATHS = Path(__file__).with_name("fca_xml_paths.csv")


def field_paths(template: str) -> pd.DataFrame:
    """Path of each field of one template, in the order of the schema."""
    p = pd.read_csv(PATHS, dtype=str, keep_default_na=False)
    p = p[p["template"] == template].copy()
    p["row"] = p["row"].astype(int)
    return p.sort_values("row")


def _parts(path: str) -> list[str]:
    return [s for s in path.split("/") if s]


def _add(parent, parts, cache, prefix=()):
    """Create (or reuse) the chain of elements `parts` under parent."""
    node = parent
    for i, tag in enumerate(parts):
        key = prefix + tuple(parts[: i + 1])
        if key not in cache:
            cache[key] = etree.SubElement(node, f"{{{NS}}}{tag}")
        node = cache[key]
    return node


def _set(leaf, value: str, xml_type: str) -> None:
    if xml_type == "YesNoIndicator":
        value = {"Y": "true", "N": "false"}[value]
    if xml_type == "ActiveOrHistoricCurrencyAndAmount":
        leaf.set("Ccy", "GBP")
    leaf.text = value


def write_report(table: pd.DataFrame, template: str, out: Path) -> None:
    paths = field_paths(template)
    report_level = paths[~paths["value_path"].str.startswith(f"/{RECORD}")]
    loan_level = paths[paths["value_path"].str.startswith(f"/{RECORD}")]
    # a path used by two field codes (RREL3 and RREC2) is written once
    loan_level = loan_level.drop_duplicates("value_path")
    report_level = report_level.drop_duplicates("value_path")

    root = etree.Element(f"{{{NS}}}Document", nsmap={None: NS})
    rpt = _add(root, [MESSAGE, "NewCrrctn", "ScrtstnRpt"], {})
    cache: dict = {}
    first = table.iloc[0]
    for f in report_level.itertuples():
        leaf = _add(rpt, _parts(f.value_path), cache)
        _set(leaf, first[f.field], f.xml_type)
    specs = [(f.field, _parts(f.value_path)[1:], _parts(f.nd_path)[1:],
              f.xml_type) for f in loan_level.itertuples()]
    for row in table[[s[0] for s in specs]].itertuples(index=False):
        rec = etree.SubElement(rpt, f"{{{NS}}}{RECORD}")
        rcache: dict = {}
        for (field, vpath, ndpath, xml_type), value in zip(specs, row):
            if value.startswith("ND") and value[2:3] in "12345":
                if not ndpath:
                    raise ValueError(f"{field} does not accept {value}")
                _add(rec, ndpath, rcache).text = value[:3]
            else:
                _set(_add(rec, vpath, rcache), value, xml_type)
    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                          pretty_print=True)
    # reports travel zipped: one XML file inside a .zip archive
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo(Path(out).stem + ".xml", (2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, data)


def _open(path: Path) -> etree._ElementTree:
    """Parse an XML report, zipped (.zip) or not (.xml)."""
    if str(path).endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            return etree.ElementTree(etree.fromstring(z.read(z.namelist()[0])))
    return etree.parse(str(path))


def _leaves(node, prefix, out):
    """Collect {path: element} for every leaf below node."""
    for child in node:
        path = f"{prefix}/{etree.QName(child).localname}"
        if len(child):
            _leaves(child, path, out)
        else:
            out[path] = child
    return out


def read_report(path: Path, template: str) -> pd.DataFrame:
    """Read the report into a table with one column per field code."""
    paths = field_paths(template)
    q = f"{{{NS}}}"
    rpt = _open(path).getroot().find(
        f"{q}{MESSAGE}/{q}NewCrrctn/{q}ScrtstnRpt")
    top = {}
    for child in rpt:
        if etree.QName(child).localname != RECORD:
            top[f"/{etree.QName(child).localname}"] = child
    specs = list(paths[["field", "value_path", "nd_path",
                        "xml_type"]].itertuples(index=False))
    rows = []
    for rec in rpt.iter(q + RECORD):
        leaves = _leaves(rec, f"/{RECORD}", {})
        values = {}
        for field, vpath, ndpath, xml_type in specs:
            el = top.get(vpath)
            if el is None:
                el = leaves.get(vpath)
            if el is None:
                el = leaves.get(ndpath)
            text = el.text if el is not None else ""
            if xml_type == "YesNoIndicator":
                text = {"true": "Y", "false": "N"}.get(text, text)
            values[field] = text
        rows.append(values)
    table = pd.DataFrame(rows)
    # columns in template order: RREL1, RREL2, ..., then RREC1, ...
    order = sorted(table.columns, key=lambda c: (c[3] != "L",
                                                 int(c[4:])))
    return table[order]


def check_rules(table: pd.DataFrame, template: str) -> list[str]:
    """Apply the FCA validation rules that concern single fields.

    The rules come from the FCA validation rules workbook: dates not
    after the data cut-off date, amounts not negative, percentages
    between 0 and 100, years between 1981 and 2099.
    """
    paths = field_paths(template)
    cutoff_field = paths.loc[paths["value_path"] == "/CutOffDt", "field"]
    cutoff = pd.Timestamp(table[cutoff_field.iloc[0]].iloc[0])
    problems = []
    for f in paths[paths["rule"] != ""].itertuples():
        s = table[f.field]
        s = s[~s.str.match(r"^ND[1-5]")]          # no-data codes pass
        if f.rule in ("not after cut-off", "in the past"):
            limit = cutoff if f.rule == "not after cut-off" else \
                pd.Timestamp.today()
            bad = pd.to_datetime(s) > limit
        else:
            x = pd.to_numeric(s)
            lo, hi = {"not negative": (0, None), "0 to 100": (0, 100),
                      "1981 to 2099": (1981, 2099)}[f.rule]
            bad = (x < lo) | ((x > hi) if hi is not None else False)
        if bad.any():
            problems.append(f"{f.field}: {int(bad.sum())} values break "
                            f"the rule '{f.rule}'")
    return problems


def validate(xml_file: Path, xsd_file: Path) -> list[str]:
    """Check a report against the FCA schema; return the errors."""
    schema = etree.XMLSchema(etree.parse(str(xsd_file)))
    ok = schema.validate(_open(xml_file))
    return [] if ok else [f"line {e.line}: {e.message}"
                          for e in schema.error_log]
