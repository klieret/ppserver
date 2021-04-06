#!/usr/bin/env python3

# std
import logging
from pathlib import Path
import json

# 3rd
from flask import Flask
from flask import render_template, redirect, send_file, request



templates = Path(__file__).resolve().parent / "templates"
statics = Path(__file__).resolve().parent / "static"


app = Flask(
    __name__, template_folder=str(templates.resolve()), static_folder=str(statics.resolve())
)


def get_relations_dot_string() -> str:
    return Path("/home/fuchur/Documents/21/git_sync/ppdata/relations.dot").read_text()


def get_vis_js() -> Path:
    p = statics / "js" / "vis-network.min.js"
    assert p.is_file(), p
    return p


@app.route("/")
def root():
    return render_template(
        "default.html",
        dotgraph=get_relations_dot_string(),
        js_path=str(Path("static") / get_vis_js().relative_to(statics))
    )


def main():
    app.logger.setLevel(logging.DEBUG)
    app.run()


if __name__ == "__main__":
    main()
