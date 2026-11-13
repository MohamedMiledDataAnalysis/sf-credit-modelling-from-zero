"""
Install Python and Set Up Your Workspace

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch00/listings.py
"""

# --- Listing 00.1 ------------------------------------
import pandas as pd

loans = pd.read_csv("data/rmbs_loans.csv")
print(loans.shape)

# --- Listing 00.2 ------------------------------------
import sfrating
print("sfrating", sfrating.__version__)
print("first column:", loans.columns[0])
print("last column:", loans.columns[-1])
