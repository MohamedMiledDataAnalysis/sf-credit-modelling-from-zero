"""Write the model results as a LaTeX report (Chapter 21)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

TEMPLATE = r"""\documentclass[11pt]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{booktabs}
\title{%(title)s}
\author{%(author)s}
\date{%(date)s}
\begin{document}
\maketitle
\section{Purpose}
%(purpose)s
\section{Rating-level assumptions}
%(levels)s
\section{Model ratings}
%(ratings)s
\section{Limitations}
%(limitations)s
\end{document}
"""


def table(df: pd.DataFrame, digits: int = 4) -> str:
    return df.to_latex(index=False, float_format=lambda x: f"{x:.{digits}f}")


def write_report(path, title, author, date, purpose, levels: pd.DataFrame,
                 ratings: pd.DataFrame, limitations: str) -> Path:
    text = TEMPLATE % {"title": title, "author": author, "date": date,
                       "purpose": purpose, "levels": table(levels),
                       "ratings": table(ratings), "limitations": limitations}
    p = Path(path)
    p.write_text(text)
    return p
