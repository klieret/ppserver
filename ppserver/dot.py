# 3rd
import pandas as pd


def df_to_dot(df: pd.DataFrame) -> str:
    out = "digraph G{\n"
    for row in df.iterrows():
        index, values = row
        actor, target, action = values.to_list()
        out += f'{actor} -> {target} [label="{action}"]\n'
    out += "}"
    return out
