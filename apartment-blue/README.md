# Apartment Blue

A dark theme for Cinnamon, MATE and Xfce with charcoal title bars, graphite window buttons and blue folder icons. See [NOTICE.md](NOTICE.md) for artwork credits.

See [DESIGN.md](DESIGN.md) for the colors and spacing.

## Install

Copy the two `Apartment-Blue` folders from the source checkout or extracted ZIP:

| Folder | Copy into |
| --- | --- |
| `themes/Apartment-Blue` | `~/.themes/` |
| `icons/Apartment-Blue` | `~/.icons/` |

Create the destination folders if they are missing. Select the theme for your desktop:

- **Cinnamon** — In **System Settings → Themes**, choose Apartment Blue for Applications, Desktop and Icons.
- **MATE** — In **Appearance → Theme → Customize**, choose Apartment Blue for Controls, Window Border and Icons.
- **Xfce** — In **Appearance**, select Apartment Blue for Style and Icons. In **Window Manager → Style**, select Apartment Blue again for window borders. For 200% scaling, also copy `themes/Apartment-Blue-HiDPI` to `~/.themes/` and select **Apartment-Blue-HiDPI** in Window Manager. Select Apartment Blue in **Notifications → Appearance** for matching banners.

To use the wallpaper, select `wallpapers/Apartment Blue.png` in your desktop's background settings.

If you install by copying, update or remove those same folders by hand. If you
prefer a script, run `python3 install.py` from this directory. It copies the
theme, icons and wallpaper and records the installation for updates and removal.

For a script-managed installation, use the new package to update or uninstall:

```sh
python3 install.py --update
python3 install.py --uninstall
```

The installer checks that the theme, icons and wallpaper still match an
installation it knows. Move modified files aside before replacing them.
The optional libadwaita override has its own apply and remove commands below.

The silver-edged window buttons are 12 pixels across at 100% scale. The glyphs
appear on hover, and in app-drawn headers they also appear on keyboard focus. The buttons follow the window manager's layout.

## Libadwaita

Linux Mint's patched libadwaita can read the theme's versioned styles for 1.5, 1.7 and 1.9. For upstream libadwaita, use the optional user stylesheet:

```sh
python3 libadwaita.py apply
python3 libadwaita.py remove
```

Use `--legacy` for libadwaita 1.5 or earlier. The default override uses CSS variables for libadwaita 1.6 and later. Both versions assume dark appearance, so remove the override before switching to light or high contrast. The host override is read by GTK 4 apps in your user session. It adds one import at the top of your GTK CSS and keeps the rest of the file intact.

For one Flatpak app, add its application ID:

```sh
python3 libadwaita.py apply --flatpak io.github.celluloid_player.Celluloid
python3 libadwaita.py remove --flatpak io.github.celluloid_player.Celluloid
```

Restart affected apps after applying or removing the override. For a Flatpak running an older libadwaita, select `--legacy` based on its runtime. The override styles the app through its own config directory.

## The rest of the desktop

The icon set covers common folders and places, a few application icons, and
common file types. Mint-X, Adwaita and hicolor supply other icons. Use the
[wallpaper SVG](wallpapers/Apartment%20Blue.svg) if you want to render it at a
different size. See the [terminal colours](extras/terminal.md) for the included profiles.

## Building and testing

After changing the libadwaita palette or title bars, regenerate the stylesheets
and native window frames, then run the package checks.

```sh
python3 tools/build.py
python3 tools/build.py --check
python3 -m unittest discover -s tests
python3 tools/package.py
```

See [desktop checks](tests/desktop.md) for the live Cinnamon checklist. The
[licence and credits](NOTICE.md) describe the artwork and source terms.
