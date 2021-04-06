#!/usr/bin/env python3

# std
from typing import Optional, Tuple, List
from pathlib import Path

# 3rd
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from diskcache import Cache

# ours

from ppserver.log import logger

cache = Cache("data")


@cache.memoize(expire=3600)
def load_from_google(names: Tuple[str, ...]) -> List[pd.DataFrame]:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        Path(__file__).parent / "../private_data/pen-and-paper-309915-e61473bc4e7a.json", scope
    )

    logger.debug("Authorizing to google")
    gc = gspread.authorize(credentials)
    logger.debug("Authorization granted")
    ret = []
    for name in names:
        logger.debug(f"Fetching {name} from google")
        wks = gc.open(name).get_worksheet(0)
        data = wks.get_all_values()
        ret.append(pd.DataFrame(data=data[1:], columns=data[0]))
        logger.debug(f"Done fetching {name} from google")
    return ret


class DataBase:
    def __init__(self):
        self._relations_df, self._persons_df = load_from_google(("relations", "characters"))
        logger.info("Database initialized")

    def get_dot_string(self) -> str:
        out = "digraph G{\n"
        for row in self._relations_df.iterrows():
            index, values = row
            actor, target, action = values.to_list()
            out += f'{actor} -> {target} [label="{action}"]\n'
        out += "}"
        return out

    def get_persons_table_html(self) -> str:
        return self._persons_df[["Name", "Description"]].to_html(classes=["data"], index=False)


if __name__ == "__main__":
    db = DataBase()
    print(db.get_dot_string())
