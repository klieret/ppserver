# 3rd
import pandas as pd


def df_to_dot(df: pd.DataFrame) -> str:
    out = "digraph G{"
    for row in df.iterrows():
        actor, target, action = row
        out += f'{actor} -> {target} [label="{action}"]'
    out += "}"
    return out