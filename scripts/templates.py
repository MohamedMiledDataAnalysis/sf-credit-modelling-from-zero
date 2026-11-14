"""Field lists of the real reporting templates used by the book's raw files.

Field codes, names and formats follow the UK securitisation disclosure
templates (FCA SECN 11/12 and PRA Securitisation Part, which keep the
codes of Commission Delegated Regulation (EU) 2020/1224 and Implementing
Regulation (EU) 2020/1225):

* Annex 2  residential real estate   RREL1-RREL84, RREC1-RREC23
* Annex 5  automobile                AUTL1-AUTL84
* Annex 12 investor report           IVSS1-IVSS44, IVSR1-IVSR10, IVSF1-IVSF6

Only the code lists the book uses are listed in CODE_LISTS.
"""

RREL = """RREL1|Unique Identifier|{ALPHANUM-28}
RREL2|Original Underlying Exposure Identifier|{ALPHANUM-1000}
RREL3|New Underlying Exposure Identifier|{ALPHANUM-1000}
RREL4|Original Obligor Identifier|{ALPHANUM-1000}
RREL5|New Obligor Identifier|{ALPHANUM-1000}
RREL6|Data Cut-Off Date|{DATEFORMAT}
RREL7|Pool Addition Date|{DATEFORMAT}
RREL8|Date Of Repurchase|{DATEFORMAT}
RREL9|Redemption Date|{DATEFORMAT}
RREL10|Resident|{Y/N}
RREL11|Geographic Region - Obligor|{NUTS}
RREL12|Geographic Region Classification|{YEAR}
RREL13|Employment Status|{LIST}
RREL14|Credit Impaired Obligor|{Y/N}
RREL15|Customer Type|{LIST}
RREL16|Primary Income|{MONETARY}
RREL17|Primary Income Type|{LIST}
RREL18|Primary Income Currency|{CURRENCYCODE_3}
RREL19|Primary Income Verification|{LIST}
RREL20|Secondary Income|{MONETARY}
RREL21|Secondary Income Verification|{LIST}
RREL22|Special Scheme|{ALPHANUM-10000}
RREL23|Origination Date|{DATEFORMAT}
RREL24|Maturity Date|{DATEFORMAT}
RREL25|Original Term|{INTEGER-9999}
RREL26|Origination Channel|{LIST}
RREL27|Purpose|{LIST}
RREL28|Currency Denomination|{CURRENCYCODE_3}
RREL29|Original Principal Balance|{MONETARY}
RREL30|Current Principal Balance|{MONETARY}
RREL31|Prior Principal Balances|{MONETARY}
RREL32|Pari Passu Underlying Exposures|{MONETARY}
RREL33|Total Credit Limit|{MONETARY}
RREL34|Purchase Price|{PERCENTAGE}
RREL35|Amortisation Type|{LIST}
RREL36|Principal Grace Period End Date|{DATEFORMAT}
RREL37|Scheduled Principal Payment Frequency|{LIST}
RREL38|Scheduled Interest Payment Frequency|{LIST}
RREL39|Payment Due|{MONETARY}
RREL40|Debt To Income Ratio|{PERCENTAGE}
RREL41|Balloon Amount|{MONETARY}
RREL42|Interest Rate Type|{LIST}
RREL43|Current Interest Rate|{PERCENTAGE}
RREL44|Current Interest Rate Index|{LIST}
RREL45|Current Interest Rate Index Tenor|{LIST}
RREL46|Current Interest Rate Margin|{PERCENTAGE}
RREL47|Interest Rate Reset Interval|{INTEGER-9999}
RREL48|Interest Rate Cap|{PERCENTAGE}
RREL49|Interest Rate Floor|{PERCENTAGE}
RREL50|Revision Margin 1|{PERCENTAGE}
RREL51|Interest Revision Date 1|{DATEFORMAT}
RREL52|Revision Margin 2|{PERCENTAGE}
RREL53|Interest Revision Date 2|{DATEFORMAT}
RREL54|Revision Margin 3|{PERCENTAGE}
RREL55|Interest Revision Date 3|{DATEFORMAT}
RREL56|Revised Interest Rate Index|{LIST}
RREL57|Revised Interest Rate Index Tenor|{LIST}
RREL58|Number Of Payments Before Securitisation|{INTEGER-9999}
RREL59|Percentage Of Prepayments Allowed Per Year|{PERCENTAGE}
RREL60|Prepayment Lock-Out End Date|{DATEFORMAT}
RREL61|Prepayment Fee|{MONETARY}
RREL62|Prepayment Fee End Date|{DATEFORMAT}
RREL63|Prepayment Date|{DATEFORMAT}
RREL64|Cumulative Prepayments|{MONETARY}
RREL65|Date Of Restructuring|{DATEFORMAT}
RREL66|Date Last In Arrears|{DATEFORMAT}
RREL67|Arrears Balance|{MONETARY}
RREL68|Number Of Days In Arrears|{INTEGER-9999}
RREL69|Account Status|{LIST}
RREL70|Reason for Default or Foreclosure|{LIST}
RREL71|Default Amount|{MONETARY}
RREL72|Default Date|{DATEFORMAT}
RREL73|Allocated Losses|{MONETARY}
RREL74|Cumulative Recoveries|{MONETARY}
RREL75|Litigation|{Y/N}
RREL76|Recourse|{Y/N}
RREL77|Deposit Amount|{MONETARY}
RREL78|Insurance Or Investment Provider|{ALPHANUM-1000}
RREL79|Original Lender Name|{ALPHANUM-100}
RREL80|Original Lender Legal Entity Identifier|{LEI}
RREL81|Original Lender Establishment Country|{COUNTRYCODE_2}
RREL82|Originator Name|{ALPHANUM-100}
RREL83|Originator Legal Entity Identifier|{LEI}
RREL84|Originator Establishment Country|{COUNTRYCODE_2}"""

RREC = """RREC1|Unique Identifier|{ALPHANUM-28}
RREC2|Underlying Exposure Identifier|{ALPHANUM-1000}
RREC3|Original Collateral Identifier|{ALPHANUM-1000}
RREC4|New Collateral Identifier|{ALPHANUM-1000}
RREC5|Collateral Type|{LIST}
RREC6|Geographic Region - Collateral|{NUTS}
RREC7|Occupancy Type|{LIST}
RREC8|Lien|{INTEGER-9999}
RREC9|Property Type|{LIST}
RREC10|Energy Performance Certificate Value|{LIST}
RREC11|Energy Performance Certificate Provider Name|{ALPHANUM-100}
RREC12|Current Loan-To-Value|{PERCENTAGE}
RREC13|Current Valuation Amount|{MONETARY}
RREC14|Current Valuation Method|{LIST}
RREC15|Current Valuation Date|{DATEFORMAT}
RREC16|Original Loan-To-Value|{PERCENTAGE}
RREC17|Original Valuation Amount|{MONETARY}
RREC18|Original Valuation Method|{LIST}
RREC19|Original Valuation Date|{DATEFORMAT}
RREC20|Date Of Sale|{DATEFORMAT}
RREC21|Sale Price|{MONETARY}
RREC22|Collateral Currency|{CURRENCYCODE_3}
RREC23|Guarantor Type|{LIST}"""

AUTL = """AUTL1|Unique Identifier|{ALPHANUM-28}
AUTL2|Original Underlying Exposure Identifier|{ALPHANUM-1000}
AUTL3|New Underlying Exposure Identifier|{ALPHANUM-1000}
AUTL4|Original Obligor Identifier|{ALPHANUM-1000}
AUTL5|New Obligor Identifier|{ALPHANUM-1000}
AUTL6|Data Cut-Off Date|{DATEFORMAT}
AUTL7|Pool Addition Date|{DATEFORMAT}
AUTL8|Date Of Repurchase|{DATEFORMAT}
AUTL9|Redemption Date|{DATEFORMAT}
AUTL10|Geographic Region - Obligor|{NUTS}
AUTL11|Geographic Region Classification|{YEAR}
AUTL12|Employment Status|{LIST}
AUTL13|Credit Impaired Obligor|{Y/N}
AUTL14|Obligor Legal Type|{LIST}
AUTL15|Customer Type|{LIST}
AUTL16|Primary Income|{MONETARY}
AUTL17|Primary Income Type|{LIST}
AUTL18|Primary Income Currency|{CURRENCYCODE_3}
AUTL19|Primary Income Verification|{LIST}
AUTL20|Revenue|{MONETARY}
AUTL21|Financial Statement Currency|{CURRENCYCODE_3}
AUTL22|Special Scheme|{ALPHANUM-10000}
AUTL23|Product Type|{LIST}
AUTL24|Origination Date|{DATEFORMAT}
AUTL25|Maturity Date|{DATEFORMAT}
AUTL26|Original Term|{INTEGER-9999}
AUTL27|Origination Channel|{LIST}
AUTL28|Currency Denomination|{CURRENCYCODE_3}
AUTL29|Original Principal Balance|{MONETARY}
AUTL30|Current Principal Balance|{MONETARY}
AUTL31|Purchase Price|{PERCENTAGE}
AUTL32|Amortisation Type|{LIST}
AUTL33|Principal Grace Period End Date|{DATEFORMAT}
AUTL34|Scheduled Principal Payment Frequency|{LIST}
AUTL35|Scheduled Interest Payment Frequency|{LIST}
AUTL36|Payment Method|{LIST}
AUTL37|Payment Due|{MONETARY}
AUTL38|Balloon Amount|{MONETARY}
AUTL39|Down Payment Amount|{MONETARY}
AUTL40|Current Interest Rate|{PERCENTAGE}
AUTL41|Current Interest Rate Index|{LIST}
AUTL42|Current Interest Rate Index Tenor|{LIST}
AUTL43|Current Interest Rate Margin|{PERCENTAGE}
AUTL44|Interest Rate Reset Interval|{INTEGER-9999}
AUTL45|Interest Rate Cap|{PERCENTAGE}
AUTL46|Interest Rate Floor|{PERCENTAGE}
AUTL47|Number Of Payments Before Securitisation|{INTEGER-9999}
AUTL48|Percentage Of Prepayments Allowed Per Year|{PERCENTAGE}
AUTL49|Prepayment Fee|{MONETARY}
AUTL50|Prepayment Fee End Date|{DATEFORMAT}
AUTL51|Prepayment Date|{DATEFORMAT}
AUTL52|Cumulative Prepayments|{MONETARY}
AUTL53|Manufacturer|{ALPHANUM-100}
AUTL54|Model|{ALPHANUM-100}
AUTL55|Year Of Registration|{YEAR}
AUTL56|New Or Used|{LIST}
AUTL57|Energy Performance Certificate Value|{LIST}
AUTL58|Energy Performance Certificate Provider Name|{ALPHANUM-100}
AUTL59|Original Loan-To-Value|{PERCENTAGE}
AUTL60|Original Valuation Amount|{MONETARY}
AUTL61|Original Residual Value Of Vehicle|{MONETARY}
AUTL62|Option To Buy Price|{MONETARY}
AUTL63|Securitised Residual Value|{MONETARY}
AUTL64|Updated Residual Value Of Vehicle|{MONETARY}
AUTL65|Date Of Updated Residual Valuation Of Vehicle|{DATEFORMAT}
AUTL66|Date Of Restructuring|{DATEFORMAT}
AUTL67|Date Last In Arrears|{DATEFORMAT}
AUTL68|Arrears Balance|{MONETARY}
AUTL69|Number Of Days In Arrears|{INTEGER-9999}
AUTL70|Account Status|{LIST}
AUTL71|Reason for Default or Foreclosure|{LIST}
AUTL72|Default Amount|{MONETARY}
AUTL73|Default Date|{DATEFORMAT}
AUTL74|Allocated Losses|{MONETARY}
AUTL75|Residual Value Losses|{MONETARY}
AUTL76|Cumulative Recoveries|{MONETARY}
AUTL77|Sale Price|{MONETARY}
AUTL78|Deposit Amount|{MONETARY}
AUTL79|Original Lender Name|{ALPHANUM-100}
AUTL80|Original Lender Legal Entity Identifier|{LEI}
AUTL81|Original Lender Establishment Country|{COUNTRYCODE_2}
AUTL82|Originator Name|{ALPHANUM-100}
AUTL83|Originator Legal Entity Identifier|{LEI}
AUTL84|Originator Establishment Country|{COUNTRYCODE_2}"""

IVSS = """IVSS1|Unique Identifier|{ALPHANUM-28}
IVSS2|Data Cut-Off Date|{DATEFORMAT}
IVSS3|Securitisation Name|{ALPHANUM-100}
IVSS4|Reporting Entity Name|{ALPHANUM-100}
IVSS5|Reporting Entity Contact Person|{ALPHANUM-256}
IVSS6|Reporting Entity Contact Telephone|{TELEPHONE}
IVSS7|Reporting Entity Contact Emails|{ALPHANUM-256}
IVSS8|Risk Retention Method|{LIST}
IVSS9|Risk Retention Holder|{LIST}
IVSS10|Underlying Exposure Type|{LIST}
IVSS11|Risk Transfer Method|{Y/N}
IVSS12|Trigger Measurements/Ratios|{Y/N}
IVSS13|Revolving/Ramp-Up Period End-Date|{DATEFORMAT}
IVSS14|Principal Recoveries In The Period|{MONETARY}
IVSS15|Interest Recoveries In The Period|{MONETARY}
IVSS16|Principal Collections In The Period|{MONETARY}
IVSS17|Interest Collections In The Period|{MONETARY}
IVSS18|Drawings Under Liquidity Facility|{Y/N}
IVSS19|Securitisation Excess Spread|{MONETARY}
IVSS20|Excess Spread Trapping Mechanism|{Y/N}
IVSS21|Current Overcollateralisation|{PERCENTAGE}
IVSS22|Annualised Constant Prepayment Rate|{PERCENTAGE}
IVSS23|Dilutions|{MONETARY}
IVSS24|Gross Charge Offs In The Period|{MONETARY}
IVSS25|Repurchased Exposures|{MONETARY}
IVSS26|Restructured Exposures|{MONETARY}
IVSS27|Annualised Constant Default Rate|{PERCENTAGE}
IVSS28|Defaulted Exposures|{MONETARY}
IVSS29|Defaulted Exposures CRR|{MONETARY}
IVSS30|Risk Weight Approach|{LIST}
IVSS31|Obligor Probability Of Default in Range [0.00%,0.10%)|{PERCENTAGE}
IVSS32|Obligor Probability Of Default in Range [0.10%,0.25%)|{PERCENTAGE}
IVSS33|Obligor Probability Of Default in Range [0.25%,1.00%)|{PERCENTAGE}
IVSS34|Obligor Probability Of Default in Range [1.00%,7.50%)|{PERCENTAGE}
IVSS35|Obligor Probability Of Default in Range [7.50%,20.00%)|{PERCENTAGE}
IVSS36|Obligor Probability Of Default in Range [20.00%,100.00%]|{PERCENTAGE}
IVSS37|Internal Loss Given Default Estimate|{PERCENTAGE}
IVSS38|Arrears 1-29 Days|{PERCENTAGE}
IVSS39|Arrears 30-59 Days|{PERCENTAGE}
IVSS40|Arrears 60-89 Days|{PERCENTAGE}
IVSS41|Arrears 90-119 Days|{PERCENTAGE}
IVSS42|Arrears 120-149 Days|{PERCENTAGE}
IVSS43|Arrears 150-179 Days|{PERCENTAGE}
IVSS44|Arrears 180+ Days|{PERCENTAGE}"""

IVSR = """IVSR1|Unique Identifier|{ALPHANUM-28}
IVSR2|Original Test/Event/Trigger Identifier|{ALPHANUM-1000}
IVSR3|New Test/Event/Trigger Identifier|{ALPHANUM-1000}
IVSR4|Description|{ALPHANUM-100000}
IVSR5|Threshold Level|{NUMERIC}
IVSR6|Actual Value|{NUMERIC}
IVSR7|Status|{Y/N}
IVSR8|Cure Period|{INTEGER-9999}
IVSR9|Calculation Frequency|{INTEGER-9999}
IVSR10|Consequence for Breach|{LIST}"""

IVSF = """IVSF1|Unique Identifier|{ALPHANUM-28}
IVSF2|Original Cashflow Item Identifier|{ALPHANUM-1000}
IVSF3|New Cashflow Item Identifier|{ALPHANUM-1000}
IVSF4|Cashflow Item|{ALPHANUM-1000}
IVSF5|Amount Paid During Period|{MONETARY}
IVSF6|Available Funds Post|{MONETARY}"""


def fields(block: str) -> list[tuple[str, str, str]]:
    """Return (code, name, format) tuples from one of the blocks above."""
    return [tuple(line.split("|")) for line in block.splitlines()]


# No-data options (Article 9(3) of Delegated Regulation 2020/1224)
ND_CODES = {
    "ND1": "Data not collected as not required by the lending or underwriting criteria",
    "ND2": "Data collected on application but not loaded into the reporting system at completion",
    "ND3": "Data collected on application but loaded onto a separate system from the reporting system",
    "ND4": "Data collected but will only be available from a later date (ND4-YYYY-MM-DD)",
    "ND5": "Not applicable",
}

# (field, code, meaning, value used by the book's model tables)
CODE_LISTS = [
    ("RREL13", "EMRS", "Employed - Private Sector", "Employed"),
    ("RREL13", "EMBL", "Employed - Public Sector", "Employed"),
    ("RREL13", "EMUK", "Employed - Sector Unknown", "Employed"),
    ("RREL13", "UNEM", "Unemployed", "Unemployed"),
    ("RREL13", "SFEM", "Self-employed", "Self-employed"),
    ("RREL13", "NOEM", "No Employment, Obligor is Legal Entity", "Other"),
    ("RREL13", "STNT", "Student", "Other"),
    ("RREL13", "PNNR", "Pensioner", "Other"),
    ("RREL15", "CNEO", "New customer and not an employee/affiliated with the originator's group", ""),
    ("RREL15", "ENEO", "Existing customer and not an employee/affiliated with the originator's group", ""),
    ("RREL26", "BRAN", "Office or Branch Network", ""),
    ("RREL26", "DRCT", "Central or Direct", ""),
    ("RREL26", "BROK", "Broker", ""),
    ("RREL26", "WEBI", "Internet", ""),
    ("RREL27", "PURC", "Purchase", ""),
    ("RREL27", "RMRT", "Remortgage", ""),
    ("RREL35", "FRXX", "French (total instalment amount is the same each period)", "Repayment"),
    ("RREL35", "DEXX", "German (first instalment interest-only, remaining instalments constant)", "Repayment"),
    ("RREL35", "FIXE", "Fixed amortisation schedule", "Repayment"),
    ("RREL35", "BLLT", "Bullet (full principal repaid in the last instalment)", "Interest-only"),
    ("RREL37", "MNTH", "Monthly", ""),
    ("RREL38", "MNTH", "Monthly", ""),
    ("RREL42", "FXRL", "Fixed rate underlying exposure (for life)", ""),
    ("RREL42", "FLCF", "Fixed rate with compulsory future switch to floating", ""),
    ("RREL42", "FLIF", "Floating rate underlying exposure (for life)", ""),
    ("RREL44", "BOER", "Bank of England Base Rate", ""),
    ("RREL56", "BOER", "Bank of England Base Rate", ""),
    ("RREL56", "LDOR", "Lender's Own Rate", ""),
    ("RREL69", "PERF", "Performing", "C"),
    ("RREL69", "ARRE", "Arrears", "arrears"),
    ("RREL69", "DFLT", "Defaulted according to Article 178 of Regulation (EU) No 575/2013", "DEF"),
    ("RREL69", "RDMD", "Redeemed", "PRE"),
    ("RREL70", "PDXX", "Any debt more than 90/180 days past due", ""),
    ("RREC5", "RBLD", "Residential Building", ""),
    ("RREC7", "FOWN", "Owner Occupied", "Owner-occupied"),
    ("RREC7", "POWN", "Partially Owner Occupied", "Owner-occupied"),
    ("RREC7", "TLET", "Non-Owner Occupied or Buy-to-Let", "Buy-to-let"),
    ("RREC7", "HOLD", "Holiday or Second Home", "Other"),
    ("RREC9", "RHOS", "Residential (House, detached or semi-detached)", "House"),
    ("RREC9", "RFLT", "Residential (Flat or Apartment)", "Flat"),
    ("RREC9", "RBGL", "Residential (Bungalow)", "Bungalow"),
    ("RREC9", "RTHS", "Residential (Terraced House)", "House"),
    ("RREC23", "NGUA", "No Guarantor", ""),
    ("RREC14", "FIEI", "Full, internal and external inspection", ""),
    ("RREC14", "IDXD", "Indexed", ""),
    ("RREC18", "FIEI", "Full, internal and external inspection", ""),
    ("AUTL14", "INDV", "Individual", ""),
    ("AUTL23", "PPUR", "(Personal) Contract Purchase", "PCP"),
    ("AUTL23", "HIRP", "Hire Purchase", "HP"),
    ("AUTL23", "PHIR", "(Personal) Contract Hire", "Other"),
    ("AUTL32", "FRXX", "French", ""),
    ("AUTL36", "CDTX", "Direct Debit", ""),
    ("AUTL56", "NEWX", "New", "New"),
    ("AUTL56", "USED", "Used", "Used"),
    ("AUTL56", "DEMO", "Demo", "Used"),
    ("AUTL70", "PERF", "Performing", "censored"),
    ("AUTL70", "ARRE", "Arrears", "censored"),
    ("AUTL70", "DFLT", "Defaulted according to Article 178 of Regulation (EU) No 575/2013", "default"),
    ("AUTL70", "RDMD", "Redeemed (censored if AUTL51 is ND5: repaid "
                       "at maturity)", "prepaid"),
    ("IVSS8", "VSLC", "Vertical slice - Article 6(3)(a)", ""),
    ("IVSS9", "ORIG", "Originator", ""),
    ("IVSS10", "RMRT", "Residential Mortgage", ""),
]

# UK NUTS 2016 codes. The template asks for NUTS3; the first three
# characters give the NUTS1 region used by the book's tables.
NUTS1 = {
    "UKC": "North East", "UKD": "North West", "UKE": "Yorkshire",
    "UKF": "East Midlands", "UKG": "West Midlands", "UKH": "East of England",
    "UKI": "London", "UKJ": "South East", "UKK": "South West",
    "UKL": "Wales", "UKM": "Scotland", "UKN": "Northern Ireland",
}
NUTS3_EXAMPLE = {  # one NUTS3 area per region for the synthetic tape
    "North East": "UKC22", "North West": "UKD33", "Yorkshire": "UKE42",
    "East Midlands": "UKF11", "West Midlands": "UKG31",
    "East of England": "UKH12", "London": "UKI31", "South East": "UKJ11",
    "South West": "UKK11", "Wales": "UKL22", "Scotland": "UKM82",
    "Northern Ireland": "UKN06",
}
