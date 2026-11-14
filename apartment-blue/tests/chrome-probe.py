"""Open one standard title bar for the Cinnamon screenshot tests."""

import sys

import gi

mode = sys.argv[1]
major = 3 if mode in ("muffin", "gtk3") else 4
gi.require_version("Gtk", f"{major}.0")
gi.require_version("Gdk", f"{major}.0")
from gi.repository import Gdk, GLib, Gtk

if mode == "adw":
    gi.require_version("Adw", "1")
    from gi.repository import Adw
    Adw.init()

title = sys.argv[2] if len(sys.argv) > 2 else f"Apartment Blue {mode}"
window = Gtk.Window(title=title, default_width=430, default_height=115)
Gtk.Settings.get_default().set_property("gtk-decoration-layout", ":minimize,maximize,close")
body = Gtk.Box()
body.set_name("chrome-probe")
provider = Gtk.CssProvider()
provider.load_from_data(b"#chrome-probe { background-color: #415465; }")
if major == 3:
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    window.add(body)
else:
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    window.set_child(body)

bar = None
if mode != "muffin":
    if mode == "gtk3":
        bar = Gtk.HeaderBar(title=title, show_close_button=True, has_subtitle=False)
    elif mode == "gtk4":
        bar = Gtk.HeaderBar()
    else:
        bar = Adw.HeaderBar()
    window.set_titlebar(bar)


def children(widget):
    if major == 3:
        items = []
        if isinstance(widget, Gtk.Container):
            widget.forall(items.append)
        return items
    items = []
    child = widget.get_first_child()
    while child is not None:
        items.append(child)
        child = child.get_next_sibling()
    return items


def title_buttons(widget):
    if isinstance(widget, Gtk.Button):
        classes = widget.get_style_context().list_classes() if major == 3 else widget.get_css_classes()
        for name in ("close", "minimize", "maximize"):
            if name in classes:
                yield name, widget
    for child in children(widget):
        yield from title_buttons(child)


def measure():
    if bar is not None:
        height = bar.get_allocated_height() if major == 3 else bar.get_height()
        if height == 0:
            return True
        print(f"{mode} title bar: {height} logical px", flush=True)
        for name, button in title_buttons(bar):
            width, height = button.get_allocated_width(), button.get_allocated_height()
            print(f"hit area {name} {width} {height}", flush=True)
    print(f"{mode} GTK window scale: {window.get_scale_factor()}", flush=True)
    return False

GLib.timeout_add(300, measure)
if major == 3:
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
else:
    loop = GLib.MainLoop()
    window.connect("close-request", lambda *_: loop.quit() or False)
    window.present()
    loop.run()
