#!/usr/bin/env python3

# std
import logging
from pathlib import Path
import json
from datetime import datetime

# 3rd
from flask import Flask
from flask import render_template, redirect, send_file, request

# ours
from ppserver.database import DataBase


templates = Path(__file__).resolve().parent / "templates"
statics = Path(__file__).resolve().parent / "static"


app = Flask(
    __name__, template_folder=str(templates.resolve()), static_folder=str(statics.resolve())
)

db = DataBase()


def get_vis_js() -> Path:
    p = statics / "js" / "vis-network.min.js"
    assert p.is_file(), p
    return p


@app.route("/")
def root():
    global db
    return render_template(
        "default.html",
        dotgraph=db.get_dot_string(),
        js_path=str(Path("static") / get_vis_js().relative_to(statics)),
        persons_table=db.get_persons_table_html(),
        not_reloaded_since=db.last_reload.strftime("%b %d %Y %H:%M:%S")
    )


@app.route("/reload")
def reload():
    global db
    db.reload(force=True)
    return root()


def main():
    app.logger.setLevel(logging.DEBUG)
    app.run(port=6149)


if __name__ == "__main__":
    main()
