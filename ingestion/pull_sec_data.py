"""
pull_sec_data.py
Fetches SVB Financial Group's structured financial data from SEC's XBRL
companyfacts API and saves it as clean, year-wise JSON files.

This script ONLY fetches, extracts, and saves numeric data.
Qualitative extraction (Items 1A/7/7A) lives in extract_qualitative.py.

Run from the project root:
    python3 pull_sec_data.py
"""

import requests
import json
import os

from config.xbrl_tags import BALANCE_SHEET, INCOME_STATEMENT, CASH_FLOW

CIK = "0000719739"  # SVB Financial Group
HEADERS = {"User-Agent": "Smrithi L 22pd33@psgtech.ac.in"}  # SEC requires a real identifying UA

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def fetch_company_facts(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def get_all_years(data, tag_or_tags):
    """
    Returns {year: value} for a given us-gaap XBRL tag (or list of candidate tags — tried in
    order, with later tags overriding earlier ones for any year both cover). This handles
    cases like SVB's 2020 CECL adoption, where the tag name used for a field changed partway
    through the filing history — pass [old_tag, new_tag] and both eras get merged automatically.
    Only annual (10-K, fp=FY) filings are used. If a tag has multiple entries for the same
    year (restatements), keeps the last one seen.
    """
    tags = tag_or_tags if isinstance(tag_or_tags, list) else [tag_or_tags]
    result = {}
    for tag in tags:
        if tag not in data["facts"].get("us-gaap", {}):
            continue
        for unit, entries in data["facts"]["us-gaap"][tag]["units"].items():
            for e in entries:
                if e.get("form") == "10-K" and e.get("fp") == "FY":
                    year = e.get("end", "")[:4]
                    if year:
                        result[year] = e.get("val")  # later tag in the list overrides earlier
    return result


def extract_year_wise(data, tag_map, label):
    """
    tag_map: {friendly_field_name: xbrl_tag_name}
    Returns data organized as {year: {field: value}} instead of {field: {year: value}} —
    this is the structure ratios.py and rules.py will consume directly.
    Prints which tags were missing so gaps are easy to spot.
    """
    field_year_values = {}
    missing = []

    for field, tag in tag_map.items():
        years = get_all_years(data, tag)
        field_year_values[field] = years
        if not years:
            missing.append((field, tag))

    # Pivot from {field: {year: value}} to {year: {field: value}}
    all_years = sorted({y for years in field_year_values.values() for y in years})
    year_wise = {year: {} for year in all_years}
    for field, years in field_year_values.items():
        for year, value in years.items():
            year_wise[year][field] = value

    print(f"\n=== {label} ===")
    for year in all_years:
        print(f"  {year}: {year_wise[year]}")
    if missing:
        print(f"  --> NOT FOUND (check data/raw/available_tags.json for the real tag name):")
        for field, tag in missing:
            print(f"      {field} (tried tag: {tag})")

    return year_wise


def main():
    print("Fetching SVB Financial Group data from SEC XBRL API...")
    data = fetch_company_facts(CIK)
    print(f"Fetched. Total us-gaap tags available: {len(data['facts'].get('us-gaap', {}))}")

    # Save raw companyfacts response
    with open(f"{RAW_DIR}/companyfacts.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved raw response to {RAW_DIR}/companyfacts.json")

    # Save every available tag name — makes debugging missing tags much easier
    available_tags = sorted(data["facts"].get("us-gaap", {}).keys())
    with open(f"{RAW_DIR}/available_tags.json", "w") as f:
        json.dump(available_tags, f, indent=2)
    print(f"Saved {len(available_tags)} available tag names to {RAW_DIR}/available_tags.json")

    # Extract each statement, year-wise
    balance_sheet = extract_year_wise(data, BALANCE_SHEET, "Balance Sheet")
    income_statement = extract_year_wise(data, INCOME_STATEMENT, "Income Statement")
    cash_flow = extract_year_wise(data, CASH_FLOW, "Cash Flow")

    with open(f"{PROCESSED_DIR}/balance_sheet.json", "w") as f:
        json.dump(balance_sheet, f, indent=2)
    with open(f"{PROCESSED_DIR}/income_statement.json", "w") as f:
        json.dump(income_statement, f, indent=2)
    with open(f"{PROCESSED_DIR}/cash_flow.json", "w") as f:
        json.dump(cash_flow, f, indent=2)

    print(f"\nSaved: balance_sheet.json, income_statement.json, cash_flow.json in {PROCESSED_DIR}/")
    print("\nCheck the 'NOT FOUND' lines above (if any) — paste them back and we'll look up the")
    print("correct tag names in available_tags.json together.")


if __name__ == "__main__":
    main()