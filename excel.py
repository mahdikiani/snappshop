import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

try:
    base_dir = Path(os.path.dirname(__file__))
except NameError:
    base_dir = Path(".")


@lru_cache
def get_df(filepath=base_dir / "Snappshop.xlsx") -> pd.DataFrame:
    # wb = get_sheet_data()
    # sheet = wb.worksheet(worksheet_name)
    # df = get_as_dataframe(sheet)
    df = pd.read_excel(filepath)
    return df


def update_excel(df, filepath: Path = base_dir / "Snappshop.xlsx"):
    if filepath.exists():
        with pd.ExcelWriter(filepath, mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, index=False)
    else:
        df.to_excel(filepath, index=False)
