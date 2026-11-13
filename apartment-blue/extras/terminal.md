# Terminal colours

Run this from the theme folder inside a GNOME Terminal session to add the
Apartment Blue profile. Choose it from the terminal's profile menu.

```sh
python3 extras/terminal/import-gnome-terminal.py
```

The profile has a full ANSI palette, plus matching cursor and selection colours.
DejaVu Sans Mono at 11 pt is a good starting point if you want the reference look.

- [Alacritty](terminal/alacritty.toml) can import the TOML file from your config.
- [kitty](terminal/kitty.conf) can include the file from kitty.conf.
- [Xresources](terminal/Xresources) can be merged with `xrdb -merge` for compatible X11 terminals.
