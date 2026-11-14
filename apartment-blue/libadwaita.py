#!/usr/bin/env python3
"""Add or remove Apartment Blue's user stylesheet import."""

import argparse
from base64 import b64encode
import hashlib
import os
import re
import stat
from pathlib import Path
from tempfile import NamedTemporaryFile


THEME = Path(__file__).resolve().parent / "themes/Apartment-Blue"
IMPORT = b'@import url("apartment-blue-libadwaita.css"); /* Apartment Blue */'
BOM = b"\xef\xbb\xbf"
# Recognize overlays from previous releases so they can be replaced or removed.
OLD_STYLESHEETS = {
    "4cf1c7b3e35363ebc57bced71f84b2696e3027e8ba5a51f3cd774b35a90890df",
    "2c72d57c0f1ff5992030f47376616a6e42ce350c2537e1ff1541d6ba3ba4de13",
    "4503fc5fe1481e17f7754a5a3e45b51497c676dde5d5b513aba595f60837a406",
    "39b15973b0086509495946795b63480d83826c223090eeb8bf67afd2da508902",
    "dc56e5ddc9e30c84cd5d4dbef57f88f4558baa0ddd54b598450f1e6b87b1a3b2",
    "f8c8aa4389283bf458465ede5e39b020b88472df5f86453eb3cb09e3712038ba",
    "2893c9e3946adeae072fe56ec391f914d20197c63cbb98b1e2b100960a53a09c",
    "4ee632358bbc9756a0f963ce1d40bfbf8ec386f424093dd253ee6af2a29a88d6",

    "e9f4fb9c42eb244d4331267442d554c7ad474df3c3369f72d14ce00e3360a514",
    "9572fd7a7d11e4949c73d91994458b88bcbbf1d067243fb403a3302d6eb14f07",
    "ecc419ecfdbca7edf401fec8c3880274861e25f7010b0eb22e3c7a67615a53a9",
    "fd7cadf4427ed9555a847d11cb2ebe32be994ec0df47952220e23d39a463b643",
    "0be0a78d438d4155ddf402c3e62052f48f5b61c90a5dd0f918749b96a231322c",
    "d572eb370073a4ae9bee9be08bbda993a1df1842bd400cea98d566efbd2ed2c6",
}


def replace_file(path, content):
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        staging = Path(temporary.name)
        temporary.write(content)
    try:
        staging.chmod(mode)
        staging.replace(path)
    finally:
        staging.unlink(missing_ok=True)


def read_file(path):
    if path.is_symlink():
        raise OSError(f"Symlink needs manual editing: {path}")
    if path.exists():
        return path.read_bytes()
    return b""


def stylesheet(legacy):
    name = "legacy.css" if legacy else "modern.css"
    palette = (THEME / "libadwaita-override" / name).read_bytes()
    chrome = (THEME / "chrome.css").read_bytes()
    buttons = (THEME / "window-controls.css").read_bytes()
    # Inline the artwork so the user stylesheet also works inside a Flatpak.
    for asset in (THEME / "titlebuttons").glob("*.svg"):
        reference = f'titlebuttons/{asset.name}'.encode()
        buttons = buttons.replace(reference, b"data:image/svg+xml;base64," + b64encode(asset.read_bytes()))
    gtk4 = (THEME / "gtk4-chrome.css").read_bytes()
    return b"\n".join((palette, chrome, buttons, gtk4))


def owned_stylesheet(content):
    return content in (stylesheet(False), stylesheet(True)) or (
        hashlib.sha256(content).hexdigest() in OLD_STYLESHEETS
    )


def change_import(config, action, legacy):
    gtk = config / "gtk.css"
    overlay = config / "apartment-blue-libadwaita.css"
    old = read_file(gtk)
    bom = BOM if old.startswith(BOM) else b""
    body = old[len(bom):]
    lines = body.splitlines(keepends=True)
    managed = [line for line in lines if line.rstrip(b"\r\n") == IMPORT]

    if action == "remove":
        if managed:
            keep = (line for line in lines if line.rstrip(b"\r\n") != IMPORT)
            replace_file(gtk, bom + b"".join(keep))
        if overlay.exists() and owned_stylesheet(read_file(overlay)):
            overlay.unlink()
        return

    new = stylesheet(legacy)
    previous = read_file(overlay)
    if overlay.exists() and not owned_stylesheet(previous):
        raise OSError(f"Existing stylesheet needs manual editing: {overlay}")

    config.mkdir(parents=True, exist_ok=True)
    already_exists = overlay.exists()
    replace_file(overlay, new)
    try:
        if not managed:
            newline = b"\r\n" if b"\r\n" in body else b"\n"
            replace_file(gtk, bom + IMPORT + newline + body)
    except OSError:
        if already_exists:
            replace_file(overlay, previous)
        else:
            overlay.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "remove"))
    parser.add_argument("--flatpak", metavar="APP_ID", help="Use one Flatpak app's GTK configuration")
    parser.add_argument("--legacy", action="store_true", help="Use libadwaita 1.5 colors with dark appearance")
    args = parser.parse_args()

    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    if not config.is_absolute():
        config = home / ".config"
    if args.flatpak:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*){2,}", args.flatpak):
            parser.error("expected a Flatpak ID such as org.gnome.Calculator")
        config = home / ".var/app" / args.flatpak / "config"

    try:
        change_import(config / "gtk-4.0", args.action, args.legacy)
    except OSError as error:
        parser.exit(1, f"{error}\n")
    print("Restart affected apps to see the change.")


if __name__ == "__main__":
    main()
