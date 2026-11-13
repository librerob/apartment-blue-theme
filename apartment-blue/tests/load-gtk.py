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
    for name in ("folder-documents", "folder-download", "folder-music", "folder-pictures", "folder-videos"):
        small = Gtk.IconTheme.get_default().lookup_icon(name, 16, 0)
        hidpi = Gtk.IconTheme.get_default().lookup_icon_for_scale(name, 16, 2, 0)
        assert hidpi and "/Apartment-Blue/16x16@2x/places/" in hidpi.get_filename(), name
        large = Gtk.IconTheme.get_default().lookup_icon(name, 48, 0)
        assert small and "/Apartment-Blue/16x16/places/" in small.get_filename(), name
        assert large and "/Apartment-Blue/scalable/places/" in large.get_filename(), name
print(f"GTK {major} stylesheet loaded")
