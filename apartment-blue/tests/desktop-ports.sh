#!/usr/bin/env bash
set -euo pipefail

# The CI screenshots use a named sample folder.
preview_home="$HOME/Robin"
mkdir -p "$preview_home"/{Desktop,Documents,Downloads,Music,Pictures,Public,Templates,Videos}

mkdir -p "$HOME/.themes" "$HOME/.icons"
cp -r themes/Apartment-Blue themes/Apartment-Blue-HiDPI "$HOME/.themes/"
cp -r icons/Apartment-Blue "$HOME/.icons/"
xdg-user-dirs-update
for folder in Desktop Documents Downloads Music Pictures Public Templates Videos; do
  kind=${folder^^}
  case "$kind" in
    DOWNLOADS) kind=DOWNLOAD ;;
    PUBLIC) kind=PUBLICSHARE ;;
  esac
  xdg-user-dirs-update --set "$kind" "$preview_home/$folder"
done
export GTK_THEME=Apartment-Blue
mkdir -p "$HOME/.config/gtk-3.0"
printf '[Settings]\ngtk-icon-theme-name=Apartment-Blue\n' >"$HOME/.config/gtk-3.0/settings.ini"
mkdir -p "$HOME/Documents" "$HOME/Downloads" "$HOME/Pictures"

# Give the WM a normal X11 window, independent of GTK headerbar settings.
case "$DESKTOP" in
  mate)
    export XDG_CURRENT_DESKTOP=MATE
    gsettings set org.mate.interface gtk-theme Apartment-Blue
    gsettings set org.mate.interface icon-theme Apartment-Blue
    gsettings set org.mate.Marco.general theme Apartment-Blue
    gsettings set org.mate.Marco.general button-layout 'menu:minimize,maximize,close'
    gsettings set org.mate.Marco.general compositing-manager false
    while IFS= read -r daemon; do
      if [[ "$daemon" == */mate-settings-daemon && -f "$daemon" && -x "$daemon" ]]; then
        "$daemon" >evidence/settings.log 2>&1 &
        break
      fi
    done < <(dpkg -L mate-settings-daemon)
    [[ -n $daemon && -f $daemon ]]
    marco >evidence/wm.log 2>&1 &
    mate-panel >evidence/panel.log 2>&1 &
    caja --no-desktop "$preview_home" >evidence/file-manager.log 2>&1 &
    file_manager=Caja
    terminal=mate-terminal
    ;;
  xfce)
    export XDG_CURRENT_DESKTOP=XFCE
    frame=Apartment-Blue
    if [[ $GDK_SCALE == 2 ]]; then frame=Apartment-Blue-HiDPI; fi
    xfconf-query -c xsettings -p /Net/ThemeName -n -t string -s Apartment-Blue
    xfconf-query -c xsettings -p /Net/IconThemeName -n -t string -s Apartment-Blue
    xfconf-query -c xsettings -p /Gdk/WindowScalingFactor -n -t int -s "$GDK_SCALE"
    xfconf-query -c xfwm4 -p /general/theme -n -t string -s "$frame"
    xfconf-query -c xfwm4 -p /general/button_layout -n -t string -s 'O|HMC'
    xfsettingsd --replace --no-daemon >evidence/settings.log 2>&1 &
    xfwm4 --compositor=off >evidence/wm.log 2>&1 &
    # Avoid the first-run panel layout prompt.
    mkdir -p "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml"
    cp /etc/xdg/xfce4/panel/default.xml "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
    xfce4-panel >evidence/panel.log 2>&1 &
    thunar "$preview_home" >evidence/file-manager.log 2>&1 &
    file_manager=Thunar
    terminal=xfce4-terminal
    ;;
esac

for attempt in {1..50}; do
  if wmctrl -m >/dev/null 2>&1; then break; fi
  sleep .2
done
wmctrl -m | tee evidence/window-manager.txt
file=
for attempt in {1..50}; do
  file=$(wmctrl -lx 2>/dev/null | awk -v app="$file_manager" 'tolower($3) ~ "[.]" tolower(app) "$" {print $1; exit}' || true)
  if [[ -n $file ]]; then break; fi
  sleep .2
done
test -n "$file"
file=$((file))
xdotool windowmove "$file" 130 115 windowactivate --sync "$file"
sleep 1
import -window root evidence/file-manager.png
xdotool mousemove --window "$file" 275 260 click 3
sleep .4
import -window root evidence/context-menu.png
xdotool key Escape

"$terminal" --title='Apartment Blue Terminal' >evidence/terminal.log 2>&1 &
sleep 1
wmctrl -l >evidence/windows.txt

xmessage -name apartment-blue-frame -title 'Apartment Blue Native Frame' -geometry 430x90+450+650 'Window manager frame' &
native=
for attempt in {1..40}; do
  native=$(wmctrl -l 2>/dev/null | awk '/Apartment Blue Native Frame$/ {print $1; exit}' || true)
  if [[ -n $native ]]; then break; fi
  sleep .25
done
test -n "$native"
native=$((native))
xdotool windowactivate --sync "$native"
sleep 1
xprop -id "$native" _NET_FRAME_EXTENTS >evidence/frame-extents.txt
# Check the decoration rather than an accidental fallback to the stock theme.
read -r x y width < <(xwininfo -id "$native" | awk '/Absolute upper-left [XY]:|Width:/ {printf "%s ", $NF} END{print ""}')
top=$(awk -F', ' '{print $3}' evidence/frame-extents.txt)
expected=$((32 * GDK_SCALE))
printf '%s at %s×: %s px top extent (expected %s)\n' "$DESKTOP" "$GDK_SCALE" "$top" "$expected"
if [[ $DESKTOP == mate ]]; then
  # Marco includes its invisible resize margin in the reported extents.
  (( top >= expected && top <= expected + 16 * GDK_SCALE ))
else
  (( top == expected ))
fi
import -window root evidence/desktop.png
import -window root -crop "${width}x${top}+${x}+$((y - top))" +repage evidence/native-frame.png
xdotool mousemove "$((x + width - 16 * GDK_SCALE))" "$((y - expected / 2))"
sleep .4
import -window root evidence/hover.png
wmctrl -ir "$(printf '0x%x' "$native")" -b add,maximized_vert,maximized_horz
for attempt in {1..20}; do
  if xprop -id "$native" _NET_WM_STATE | grep -q _NET_WM_STATE_MAXIMIZED_HORZ; then break; fi
  sleep .2
done
xprop -id "$native" _NET_WM_STATE | grep _NET_WM_STATE_MAXIMIZED_HORZ
import -window root evidence/maximized.png

if grep -Ei 'theme parser error|failed to import|failed to load theme|theme.*(invalid|missing)' evidence/*.log; then
  exit 1
fi
