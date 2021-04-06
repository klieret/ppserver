#!/usr/bin/env python3

# std
from typing import Optional
from pathlib import Path

# 3rd
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def load_from_google(name: str) -> pd.DataFrame:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        Path(__file__).parent / "../private_data/pen-and-paper-309915-e61473bc4e7a.json", scope
    )

    gc = gspread.authorize(credentials)
    wks = gc.open(name).get_worksheet(0)
    data = wks.get_all_values()
    df = pd.DataFrame(data=data[1:], columns=data[0])

    return df


class DataBase:
    def __init__(self):
        self.relations_df: pd.DataFrame = load_from_google("characters")
        self.persons_df: pd.DataFrame = load_from_google("relations")


if __name__ == "__main__":
    db = DataBase()