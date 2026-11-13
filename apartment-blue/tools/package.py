#!/usr/bin/env python3
"""Build the install ZIP from the source tree."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
INCLUDE = (
    "themes", "icons", "wallpapers", "extras", "palette", "tests", "tools",
    "VERSION", "LICENSE", "NOTICE.md", "README.md", "CHANGELOG.md", "DESIGN.md",
    "install.py", "legacy-installs.json", "libadwaita.py",
)


def main():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = ROOT / "dist" / f"apartment-blue-v{version}.zip"
    output.parent.mkdir(exist_ok=True)

    with ZipFile(output, "w") as archive:
        for name in INCLUDE:
            path = ROOT / name
            files = sorted(path.rglob("*"), key=lambda item: item.as_posix()) if path.is_dir() else [path]
            for file in files:
                relative = file.relative_to(ROOT)
                if "__pycache__" in relative.parts or not file.is_file():
                    continue
                info = ZipInfo(f"apartment-blue/{relative.as_posix()}")
                info.compress_type = ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, file.read_bytes())
    print(output)


if __name__ == "__main__":
    main()
