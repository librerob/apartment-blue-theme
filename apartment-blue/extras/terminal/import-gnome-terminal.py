#!/usr/bin/env python3
"""Add an Apartment Blue profile alongside existing GNOME Terminal profiles."""

from ast import literal_eval
from pathlib import Path
import subprocess
import sys
from uuid import uuid4


SCHEMA = "org.gnome.Terminal.ProfilesList"
PROFILES = "/org/gnome/terminal/legacy/profiles:/"


def main():
    profile = str(uuid4())
    path = f"{PROFILES}:{profile}/"
    settings = Path(__file__).with_name("gnome-terminal.dconf").read_bytes()
    raw = subprocess.check_output(["gsettings", "get", SCHEMA, "list"], text=True).strip()
    profiles = literal_eval(raw.removeprefix("@as "))
    subprocess.run(["dconf", "load", path], input=settings, check=True)
    try:
        subprocess.run(["gsettings", "set", SCHEMA, "list", repr([*profiles, profile])], check=True)
    except subprocess.CalledProcessError:
        subprocess.run(["dconf", "reset", "-f", path], check=False)
        raise
    print("Select Apartment Blue from the GNOME Terminal profile menu.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        sys.exit(str(error))
