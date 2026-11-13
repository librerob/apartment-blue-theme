"""Parse the installed GTK stylesheet and check the theme's icon lookup."""

from pathlib import Path
import sys

import gi


major = sys.argv[1]
gi.require_version("Gtk", major + ".0")
from gi.repository import Gtk

Gtk.init()
provider = Gtk.CssProvider()
errors = []
provider.connect("parsing-error", lambda _, section, error: errors.append(error.message))
theme = Path.home() / ".themes/Apartment-Blue"
provider.load_from_path(str(theme / f"gtk-{major}.0/gtk.css"))
if errors:
    raise SystemExit("\n".join(errors))
if major == "3":
    icon = Gtk.IconTheme.get_default().lookup_icon("folder", 48, 0)
    assert icon and "/.icons/Apartment-Blue/" in icon.get_filename()
print(f"GTK {major} stylesheet loaded")
