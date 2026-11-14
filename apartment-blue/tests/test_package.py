import configparser
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "themes/Apartment-Blue"
ICONS = ROOT / "icons/Apartment-Blue"


class PackageTest(unittest.TestCase):
    def test_title_button_geometry(self):
        controls = ("close", "minimize", "maximize", "restore")
        states = {"-rest": "#9ba1a8", "-unfocused": "#747a81",
                  "": "#e3e6e9", "-pressed": "#e3e6e9"}
        ns = {"svg": "http://www.w3.org/2000/svg"}
        circles = []
        for control in controls:
            glyphs = set()
            for suffix, stroke in states.items():
                name = f"{control}{suffix}"
                with self.subTest(state=name):
                    root = ET.parse(THEME / f"titlebuttons/{name}.svg").getroot()
                    self.assertEqual((root.get("width"), root.get("height")), ("64", "64"))
                    self.assertEqual(root.get("viewBox"), "0 0 16 16")
                    circle, = root.findall(".//svg:circle", ns)
                    circles.append(tuple(circle.get(key) for key in ("cx", "cy", "r", "stroke-width")))
                    glyph, = root.findall(".//svg:path", ns)
                    self.assertEqual(glyph.get("stroke"), stroke)
                    glyphs.add(glyph.get("d"))
            self.assertEqual(len(glyphs), 1)
        self.assertEqual(set(circles), {("8", "8", "7", None)})

    def test_css_imports(self):
        for path in THEME.rglob("*.css"):
            with self.subTest(path=path.relative_to(THEME)):
                css = path.read_text(encoding="utf-8")
                self.assertEqual(css.count("{"), css.count("}"))
                for target in re.findall(r'@import url\("([^"]+)"\)', css):
                    if not target.startswith("resource:"):
                        self.assertTrue((path.parent / target).is_file(), target)

    def test_icon_index_and_folder_artwork(self):
        index = configparser.ConfigParser()
        index.read(ICONS / "index.theme")
        config = index["Icon Theme"]
        self.assertEqual(config["Inherits"], "Mint-X,Adwaita,hicolor")
        for directory in config["Directories"].split(","):
            self.assertGreater(int(index[directory]["Size"]), 0)
            files = list((ICONS / directory).glob("*.svg"))
            self.assertTrue(files, directory)
            for path in files:
                with self.subTest(icon=path.name):
                    tree = ET.parse(path)
                    self.assertIn("viewBox", tree.getroot().attrib)
                    ids = {element.get("id") for element in tree.iter()}
                    self.assertLessEqual(set(re.findall(r"url\(#([^)]+)\)", path.read_text())), ids)
        for name in ("documents", "download", "music", "pictures", "videos", "publicshare", "templates", "saved-search"):
            self.assertTrue((ICONS / f"scalable/places/folder-{name}.svg").is_file())

    def run_tool(self, home, script, *args, success=True):
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                   XDG_CONFIG_HOME=str(home / "config"), XDG_DATA_HOME=str(home / "data"))
        return subprocess.run([sys.executable, str(ROOT / script), *args],
                              env=env, capture_output=True, check=success)

    def test_install_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            self.run_tool(home, "install.py")
            self.assertTrue((home / ".themes/Apartment-Blue/window-controls.css").is_file())
            self.assertTrue((home / ".icons/Apartment-Blue/index.theme").is_file())
            self.assertTrue((home / "data/backgrounds/Apartment Blue.png").is_file())
            result = self.run_tool(home, "install.py", success=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"already exists", result.stderr)

    def test_update_and_uninstall_preserve_local_edits(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            self.run_tool(home, "install.py")
            self.run_tool(home, "install.py", "--update")
            controls = home / ".themes/Apartment-Blue/window-controls.css"
            original = controls.read_bytes()
            edited = original + b"\n/* my CSS */\n"
            controls.write_bytes(edited)
            for option in ("--update", "--uninstall"):
                result = self.run_tool(home, "install.py", option, success=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"differs from the original", result.stderr)
                self.assertEqual(controls.read_bytes(), edited)
            controls.write_bytes(original)
            self.run_tool(home, "install.py", "--uninstall")
            self.assertFalse(controls.exists())
            self.assertFalse((home / ".icons/Apartment-Blue").exists())
            self.assertFalse((home / "data/backgrounds/Apartment Blue.png").exists())

    def test_rollback_when_icon_destination_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / ".icons").write_text("keep me")
            result = self.run_tool(home, "install.py", success=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((home / ".themes/Apartment-Blue").exists())
            self.assertEqual((home / ".icons").read_text(), "keep me")

    def test_host_override_preserves_existing_css(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            css = home / "config/gtk-4.0/gtk.css"
            css.parent.mkdir(parents=True)
            original = b"\xef\xbb\xbf/* Existing settings */\r\nlabel { color: red; }"
            css.write_bytes(original)
            self.run_tool(home, "libadwaita.py", "apply")
            self.run_tool(home, "libadwaita.py", "apply")
            self.assertEqual(css.read_bytes().count(b"@import"), 1)
            self.run_tool(home, "libadwaita.py", "remove")
            self.assertEqual(css.read_bytes(), original)
            self.assertFalse((css.parent / "apartment-blue-libadwaita.css").exists())

    def test_flatpak_override_only_touches_the_named_app(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            app = "org.gnome.Calculator"
            args = ("--flatpak", app)
            self.run_tool(home, "libadwaita.py", "apply", "--legacy", *args)
            css = home / ".var/app" / app / "config/gtk-4.0/gtk.css"
            self.assertTrue(css.is_file())
            self.assertFalse((home / "config").exists())
            overlay = css.parent / "apartment-blue-libadwaita.css"
            self.assertIn(b"@define-color", overlay.read_bytes())
            overlay.write_bytes(b"/* local changes */")
            result = self.run_tool(home, "libadwaita.py", "apply", *args, success=False)
            self.assertNotEqual(result.returncode, 0)
            self.run_tool(home, "libadwaita.py", "remove", *args)
            self.assertEqual(overlay.read_bytes(), b"/* local changes */")


if __name__ == "__main__":
    unittest.main()
