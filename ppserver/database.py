#!/usr/bin/env python3

# std
from typing import Tuple, List, Dict
from pathlib import Path
from datetime import datetime

# 3rd
import pandas as pd
import gspread
from diskcache import Cache

# ours

from ppserver.log import logger

cache = Cache("data")


@cache.memoize()
def load_from_google(names: Tuple[str, ...]) -> List[pd.DataFrame]:
    logger.debug("Authorizing to google")
    filename = Path(__file__).parent / "../private_data/pen-and-paper-309915-e61473bc4e7a.json"
    assert filename.is_file()
    gc = gspread.service_account(filename=str(filename.resolve()))

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
    def __init__(self, name: str, description: str = "", alive=True, location: str = "", appeared: str = "", is_player=False):
        self.name = name
        self.description = description
        self.alive = alive
        self.locations = location.split(",")
        self.appeared = appeared
        #: Player or NPC?
        self.is_player = is_player

    @property
    def normalized_description(self):
        return self.description.replace('"','').replace("'","")

    def get_html_name(self):
        if not self.alive:
            return "<del>{name}</del>".format(name=self.name)
        if self.is_player:
            return "<b>{name}</b>".format(name=self.name)
        return self.name


def df_to_persons(df: pd.DataFrame) -> Dict[str, Person]:
    persons = {}
    print(df.columns)
    for row in df.iterrows():
        index, values = row
        values = values.to_dict()
        key = values["Name"].lower()
        keywords = [x.lower() for x in values["Keywords"].split(",")]
        persons[key] = Person(
            name=values["Name"],
            description=values["Description"],
            alive="dead" not in keywords,
            location=values["Locations"],
            appeared=values["Appeared"],
            is_player="player" in keywords,
        )
    return persons


def persons_list_to_html(persons: List[Person]) -> str:
    df = pd.DataFrame()

    df["Name"] = [p.get_html_name() for p in persons]
    df["_name"] = [p.name for p in persons]
    df["Description"] = [p.description for p in persons]
    return df.sort_values("_name")[["Name", "Description"]].to_html(
        classes=["datatable"], index=False, escape=False).replace(
        'style="text-align: right;"', "")


class DataBase:
    def __init__(self):
        self.reload()
        self.last_reload = datetime.now()

    def reload(self, force=False):
        if force:
            cache.clear()
        self._relations_df, _persons_df = load_from_google(("relations", "characters"))
        self._key2info = df_to_persons(_persons_df)
        if force:
            self.last_reload = datetime.now()

    def dot_node_for_person(self, key: str):
        person = self.get_person(key)
        return '"{key}" [title="{description}",label="{label}"]\n'.format(key=key, description=person.normalized_description, label=person.name)

    def get_dot_string(self) -> str:
        out = "digraph G{\n"
        out += "node [style=filled,shape=box,color=#009879,fillcolor=#8DE2D1,fontcolor=black]\n"
        out += "edge [color=black]"
        nodes_added = []
        for row in self._relations_df.iterrows():
            index, values = row
            values = values.to_dict()
            actor = values["Actor"]
            action = values["Relation"]
            target = values["Target"]
            arrow = "->"
            extra_props = ""
            extras = values["Extra"].split(",")
            if "bi" in extras:
                arrow = "--"
            if "?" in extras:
                extra_props +=",style=dashed"
            if actor not in nodes_added:
                out += self.dot_node_for_person(actor)
                nodes_added.append(actor)
            if target not in nodes_added:
                out += self.dot_node_for_person(target)
                nodes_added.append(target)
            out += '"{actor}" {arrow} "{target}" [label="{action}"{extra_props}]\n'.format(actor=actor, target=target, action=action, arrow=arrow, extra_props=extra_props)
        out += "}"
        logger.debug(out)
        return out

    def get_persons_table_html(self) -> str:
        return persons_list_to_html(list(self._key2info.values()))

    def get_person(self, key):
        try:
            return self._key2info[key.lower()]
        except KeyError:
            logger.warning("Don't have record about {key}".format(key=key))
            return Person(name=key)


if __name__ == "__main__":
    db = DataBase()
    print(db.get_dot_string())
