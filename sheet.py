import os
from functools import lru_cache
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2 import service_account
from gspread_dataframe import get_as_dataframe, set_with_dataframe

try:
    base_dir = Path(os.path.dirname(__file__))
except NameError:
    base_dir = Path(".")


@lru_cache
def get_sheet_data(spreadsheet_id="1sWOYcFiMFY0cxNBvK6Uc96exT7ZXhR5dpV6DnB1kcaQ"):
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://spreadsheets.google.com/feeds",
    ]
    credentials = service_account.Credentials.from_service_account_file(
        base_dir / "secrets" / "snappshop-access.json", scopes=scopes
    )

    gc = gspread.authorize(credentials)

    wb = gc.open_by_key(spreadsheet_id)
    return wb


@lru_cache
def get_df(worksheet_name="Sheet1") -> pd.DataFrame:
    wb = get_sheet_data()
    sheet = wb.worksheet(worksheet_name)
    df = get_as_dataframe(sheet)
    return df


def update_sheet_row(index: int, new_data: dict, worksheet_name="Sheet1"):
    # Get the worksheet
    wb = get_sheet_data()
    sheet = wb.worksheet(worksheet_name)

    # Convert worksheet to dataframe
    df = get_as_dataframe(sheet)

    # Update the dataframe with new data
    for key, value in new_data.items():
        if key in df.columns:
            df.at[index, key] = value
        else:
            df[key] = pd.NA
            df.at[index, key] = value

    # Clear the worksheet and write the updated dataframe back
    sheet.clear()
    set_with_dataframe(sheet, df)
