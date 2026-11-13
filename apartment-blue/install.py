#!/usr/bin/env python3
"""Install, update or remove Apartment Blue for the current user."""

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from uuid import uuid4


ROOT = Path(__file__).resolve().parent
MANIFEST = ".apartment-blue-install.json"


def fingerprint(path, ignore_manifest=False):
    """Identify file contents and relative paths without following symlinks."""
    if path.is_symlink():
        raise OSError(f"Symlink needs manual handling: {path}")
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if not path.is_dir():
        raise OSError(f"Missing installation file: {path}")

    digest = hashlib.sha256()
    for entry in sorted(path.rglob("*"), key=lambda item: item.relative_to(path).as_posix()):
        name = entry.relative_to(path).as_posix()
        if entry.is_symlink():
            raise OSError(f"Symlink needs manual handling: {entry}")
        if ignore_manifest and name == MANIFEST and entry.is_file():
            continue
        if entry.is_file():
            digest.update(f"{name}\0{fingerprint(entry)}\n".encode("utf-8"))
        elif not entry.is_dir():
            raise OSError(f"Unexpected installation file: {entry}")
    return digest.hexdigest()


def verify_installation(targets):
    current = [fingerprint(target, ignore_manifest=(index == 0))
               for index, target in enumerate(targets)]
    manifest = targets[0] / MANIFEST
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as error:
            raise OSError(f"Invalid installation manifest: {manifest}") from error
        if data == current:
            return
    else:
        legacy = json.loads((ROOT / "legacy-installs.json").read_text(encoding="utf-8"))
        if current in legacy:
            return
    raise OSError("The installed theme differs from the original package. Move it aside to keep your edits.")


def apply(sources, targets, action):
    if action == "install":
        for target in targets:
            if target.exists() or target.is_symlink():
                raise OSError(f"Destination already exists: {target}. Use --update for a previous install.")
    else:
        verify_installation(targets)

    with ExitStack() as cleanup:
        staged = []
        if action != "uninstall":
            for source, target in zip(sources, targets):
                target.parent.mkdir(parents=True, exist_ok=True)
                staging = Path(cleanup.enter_context(TemporaryDirectory(dir=target.parent))) / target.name
                if source.is_dir():
                    shutil.copytree(source, staging)
                else:
                    shutil.copyfile(source, staging)
                staged.append(staging)
            hashes = [fingerprint(path) for path in staged]
            (staged[0] / MANIFEST).write_text(json.dumps(hashes) + "\n", encoding="utf-8")

        backups = {}
        installed = []
        try:
            if action != "install":
                for target in targets:
                    backup = target.with_name(f".{target.name}.backup-{uuid4().hex}")
                    target.rename(backup)
                    backups[target] = backup
            for path, target in zip(staged, targets):
                path.rename(target)
                installed.append((path, target))
        except OSError:
            for path, target in reversed(installed):
                target.rename(path)
            for target, backup in reversed(backups.items()):
                backup.rename(target)
            raise

        for backup in backups.values():
            if backup.is_dir():
                shutil.rmtree(backup)
            else:
                backup.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--update", dest="action", action="store_const", const="update")
    options.add_argument("--uninstall", dest="action", action="store_const", const="uninstall")
    parser.set_defaults(action="install")
    args = parser.parse_args()

    home = Path.home()
    data_home = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    if not data_home.is_absolute():
        data_home = home / ".local/share"

    sources = [ROOT / name for name in (
        "themes/Apartment-Blue", "icons/Apartment-Blue", "wallpapers/Apartment Blue.png",
    )]
    targets = [
        home / ".themes/Apartment-Blue",
        home / ".icons/Apartment-Blue",
        data_home / "backgrounds/Apartment Blue.png",
    ]
    lock = targets[0].parent / ".apartment-blue-install.lock"
    try:
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock.mkdir()
        except FileExistsError as error:
            raise OSError(f"Another Apartment Blue operation may be running: {lock}") from error
        try:
            apply(sources, targets, args.action)
        finally:
            lock.rmdir()
    except OSError as error:
        parser.exit(1, f"{error}\n")

    for target in targets:
        print(target)
    if args.action == "uninstall":
        print("Removed Apartment Blue.")
    else:
        print("Choose Apartment Blue in System Settings > Themes.")


if __name__ == "__main__":
    main()
