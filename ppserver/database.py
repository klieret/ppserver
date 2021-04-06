#!/usr/bin/env python3

# std
from typing import Optional, Tuple, List, NamedTuple, Dict
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
        logger.debug("Fetching {name} from google".format(name=name))
        wks = gc.open(name).get_worksheet(0)
        data = wks.get_all_values()
        ret.append(pd.DataFrame(data=data[1:], columns=data[0]))
        logger.debug("Done fetching {name} from google".format(name=name))
    return ret


class Person:
    def __init__(self, name: str, description: str = "", alive=True, location: str = "", appeared: str = ""):
        self.name = name
        self.description = description
        self.alive = alive
        self.locations = location.split(",")
        self.appeared = appeared

    @property
    def normalized_description(self):
        return self.description.replace('"','').replace("'","")


def df_to_persons(df: pd.DataFrame) -> Dict[str, Person]:
    persons = {}
    print(df.columns)
    for row in df.iterrows():
        index, values = row
        values = values.to_dict()
        key = values["Key"]
        persons[key] = Person(
            name=values["Name"],
            description=values["Description"],
            alive=values["Alive"],
            location=values["Locations"],
            appeared = values["Appeared"]
        )
    return persons


class DataBase:
    def __init__(self):
        self._relations_df, self._persons_df = load_from_google(("relations", "characters"))
        logger.info("Database initialized")
        self._key2info = df_to_persons(self._persons_df)

    def dot_node_for_person(self, key: str):
        person = self.get_person(key)
        return '{key} [title="{description}",label="{label}"]\n'.format(key=key, description=person.normalized_description, label=person.name)

    def get_dot_string(self) -> str:
        out = "digraph G{\n"
        nodes_added = []
        for row in self._relations_df.iterrows():
            index, values = row
            actor, target, action = values.to_list()
            if actor not in nodes_added:
                out += self.dot_node_for_person(actor)
                nodes_added.append(actor)
            if target not in nodes_added:
                out += self.dot_node_for_person(target)
                nodes_added.append(target)
            out += '"{actor}" -> "{target}" [label="{action}"]\n'.format(actor=actor, target=target, action=action)
        out += "}"
        logger.debug(out)
        return out

    def get_persons_table_html(self) -> str:
        return self._persons_df[["Name", "Description"]].sort_values("Name").to_html(classes=["datatable"], index=False)

    def get_person(self, key):
        try:
            return self._key2info[key]
        except KeyError:
            logger.warning("Don't have record about {key}".format(key=key))
            return Person(name=key)


if __name__ == "__main__":
    db = DataBase()
    print(db.get_dot_string())
