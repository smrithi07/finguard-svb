"""
config/xbrl_tags.py
XBRL tag name mappings for SVB Financial Group's SEC filings.
Keys are the friendly field names used throughout FinGuard; values are the
us-gaap XBRL tag names to look up in SEC's companyfacts API.

If a tag comes back "NOT FOUND" when pull_sec_data.py runs, check
data/raw/available_tags.json for the actual tag name SVB used, and update
the mapping here.
"""

BALANCE_SHEET = {
    "cash_and_cash_equivalents": "CashAndCashEquivalentsAtCarryingValue",
    "available_for_sale_securities": "AvailableForSaleSecuritiesDebtSecurities",  # this IS fair value under GAAP
    "afs_amortized_cost": "AvailableForSaleSecuritiesAmortizedCost",
    "gross_unrealized_loss_afs": "AvailableForSaleDebtSecuritiesAccumulatedGrossUnrealizedLossBeforeTax",  # direct — no subtraction needed
    "held_to_maturity_securities": "HeldToMaturitySecurities",  # book/carrying value
    "htm_fair_value": "HeldToMaturitySecuritiesFairValue",
    "gross_unrealized_loss_htm": "HeldToMaturitySecuritiesAccumulatedUnrecognizedHoldingLoss",  # direct — most important IR risk number
    "total_loans": [
        "LoansAndLeasesReceivableNetReportedAmount",       # pre-2020 (pre-CECL)
        "FinancingReceivableBeforeAllowanceForCreditLossAndFee",  # 2020+ (CECL-era), if reported as one total
        "FinancingReceivable",                              # generic base tag, last resort
    ],
    "allowance_for_credit_losses": [
        "LoansAndLeasesReceivableAllowance",                # pre-2020 (pre-CECL)
        "FinancingReceivableAllowanceForCreditLosses",       # 2020+ (CECL-era)
    ],
    "total_assets": "Assets",
    "total_deposits": "Deposits",
    "total_liabilities": "Liabilities",
    "total_shareholders_equity": "StockholdersEquity",
    "short_term_borrowings": "ShortTermBorrowings",
    "long_term_debt": "LongTermDebt",
    # cet1_ratio intentionally omitted — SVB has NO Tier1/CET1 tags in available_tags.json at all.
    # This is a real data gap, not a wrong tag name. Look it up manually in the 10-K's
    # Regulatory Capital note and add it to svb.json by hand.
}

INCOME_STATEMENT = {
    "interest_income": "InterestAndDividendIncomeOperating",
    "interest_expense": "InterestExpense",
    "net_interest_income": "InterestIncomeExpenseNet",
    "provision_for_credit_losses": "ProvisionForLoanLeaseAndOtherLosses",
    "non_interest_income": "NoninterestIncome",
    "non_interest_expense": "NoninterestExpense",
    "income_before_tax": "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "net_income": "NetIncomeLoss",
    "earnings_per_share": "EarningsPerShareDiluted",
}

CASH_FLOW = {
    "net_cash_from_operating_activities": "NetCashProvidedByUsedInOperatingActivities",
    "net_cash_from_investing_activities": "NetCashProvidedByUsedInInvestingActivities",
    "net_cash_from_financing_activities": "NetCashProvidedByUsedInFinancingActivities",
    "net_change_in_cash": "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
    "cash_end_of_year": "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
}

# NOTE: SVB adopted CECL accounting (ASU 2016-13) in fiscal year 2020, which changed the
# XBRL tag names used for loan-related fields starting that year. total_loans and
# allowance_for_credit_losses above are lists of candidate tags (pre-CECL name first,
# CECL-era name second) rather than single strings, to cover both eras in one pull.