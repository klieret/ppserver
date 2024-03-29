# std
from typing import Tuple, List, Dict
from datetime import datetime
from pathlib import Path

# 3rd
import pandas as pd
import gspread
from diskcache import Cache

# ours
from ppserver.log import logger
from ppserver.config import config

cache = Cache("data")


@cache.memoize()
def load_from_google(names: Tuple[str, ...]) -> List[pd.DataFrame]:
    logger.debug("Authorizing to google")
    filename = Path(config["certificate_path"])
    assert filename.is_file(), filename
    gc = gspread.service_account(filename=str(filename.resolve()))

    logger.debug("Authorization granted")
    ret = []
    for name in names:
        logger.debug(f"Fetching {name} from google")
        wks = gc.open(name).get_worksheet(0)
        data = wks.get_all_values()
        ret.append(pd.DataFrame(data=data[1:], columns=data[0]))
        logger.debug(f"Done fetching {name} from google")
    return ret


class Person:
    def __init__(
        self,
        name: str,
        description: str = "",
        alive=True,
        location: str = "",
        appeared: str = "",
        race: str = "",
        is_player=False,
    ):
        self.name = name
        self.description = description
        self.alive = alive
        self.locations = location.split(",")
        self.appeared = appeared
        self.race = race
        #: Player or NPC?
        self.is_player = is_player

    @property
    def normalized_description(self):
        return self.description.replace('"', "").replace("'", "")

    def get_html_name(self):
        if not self.alive:
            return f"<del>{self.name}</del>"
        if self.is_player:
            return f"<b>{self.name}</b>"
        return self.name

    def get_html_locations(self):
        return ", ".join([loc.capitalize() for loc in self.locations])


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
            race=values["Race"],
        )
    return persons


def persons_list_to_html(persons: List[Person]) -> str:
    df = pd.DataFrame(
        [
            (
                p.get_html_name(),
                p.name,
                p.race,
                p.get_html_locations(),
                p.appeared,
                p.description,
            )
            for p in persons
        ],
        columns=[
            "Name",
            "_name",
            "Race",
            "Locations",
            "Appeared",
            "Description",
        ],
    )

    with pd.option_context("display.max_colwidth", None):
        html = (
            df.sort_values("_name")[
                [c for c in df.columns if not c.startswith("_")]
            ]
            .to_html(
                classes=["personstable", "display"],
                index=False,
                escape=False,
                table_id="persons_table",
            )
            .replace('style="text-align: right;"', "")
        )
    html = html.replace(
        "<thead>",
        "<colgroup>"
        "<col style='width: 15% !important;'>"
        "<col style='width: 10% !important;'>"
        "<col style='width: 10% !important;'>"
        "<col style='width: 10% !important;'>"
        "<col style='width: 55% !important;'>"
        "</colgroup><thead>",
    )
    return html


class DataBase:
    def __init__(self):
        self._relations_df: pd.DataFrame = None  # type: ignore
        self._key2info: Dict[str, Person] = None  # type: ignore
        self.reload()
        self.last_reload = datetime.now()

    def reload(self, force=False):
        if force:
            cache.clear()
        self._relations_df, _persons_df = load_from_google(
            (config["relations_sheet_name"], config["character_sheet_name"])
        )
        self._key2info = df_to_persons(_persons_df)
        if force:
            self.last_reload = datetime.now()

    @property
    def n_persons(self) -> int:
        return len(self._key2info)

    @property
    def n_connections(self) -> int:
        return len(self._relations_df)

    def dot_node_for_person(self, key: str):
        person = self.get_person(key)
        return (
            f'"{key}" [title="{person.normalized_description}",'
            f'label="{person.name}"]\n'
        )

    def get_dot_string(self) -> str:
        out = "digraph G{\n"
        out += (
            "node [style=filled,shape=box,color=#009879,"
            "fillcolor=#8DE2D1,fontcolor=black]\n"
        )
        out += "edge [color=black]"
        nodes_added = []
        for row in self._relations_df.iterrows():
            index, values = row
            values = values.to_dict()
            actor = values["Actor"].lower()
            action = values["Relation"]
            target = values["Target"].lower()
            arrow = "->"
            extra_props = ""
            extras = values["Extra"].split(",")
            if "bi" in extras:
                arrow = "--"
            if "?" in extras:
                extra_props += ",style=dashed"
            if actor not in nodes_added:
                out += self.dot_node_for_person(actor)
                nodes_added.append(actor)
            if target not in nodes_added:
                out += self.dot_node_for_person(target)
                nodes_added.append(target)
            out += (
                f'"{actor}" {arrow} "{target}" '
                f'[label="{action}"{extra_props}]\n'
            )
        out += "}"
        logger.debug(out)
        return out

    def get_persons_table_html(self) -> str:
        return persons_list_to_html(list(self._key2info.values()))

    def get_person(self, key):
        try:
            return self._key2info[key.lower()]
        except KeyError:
            logger.warning(f"Don't have record about {key}")
            return Person(name=key)


if __name__ == "__main__":
    db = DataBase()
    print(db.get_dot_string())
