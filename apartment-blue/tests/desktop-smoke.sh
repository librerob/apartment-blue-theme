#!/usr/bin/env bash
set -eu

# The CI screenshots use a named sample folder.
preview_home="$HOME/Robin"
mkdir -p "$preview_home"/{Desktop,Documents,Downloads,Music,Pictures,Public,Templates,Videos}

export GDK_SCALE="$SCALE" GTK_THEME=Apartment-Blue
export XDG_CURRENT_DESKTOP=X-Cinnamon XDG_SESSION_TYPE=x11 GDK_BACKEND=x11
dbus-update-activation-environment DISPLAY XAUTHORITY GDK_SCALE GTK_THEME \
  XDG_CURRENT_DESKTOP XDG_SESSION_TYPE GDK_BACKEND
mkdir -p "$HOME/.config/gtk-3.0" "$HOME"/{Documents,Downloads,Music,Pictures,Public,Templates,Videos}
cat > "$HOME/.config/gtk-3.0/settings.ini" <<'GTK'
[Settings]
gtk-theme-name=Apartment-Blue
gtk-icon-theme-name=Apartment-Blue
GTK
xdg-user-dirs-update
for folder in Desktop Documents Downloads Music Pictures Public Templates Videos; do
  kind=${folder^^}
  case "$kind" in
    DOWNLOADS) kind=DOWNLOAD ;;
    PUBLIC) kind=PUBLICSHARE ;;
  esac
  xdg-user-dirs-update --set "$kind" "$preview_home/$folder"
done
gsettings set org.cinnamon.desktop.interface scaling-factor "$SCALE"
gsettings set org.cinnamon.theme name Apartment-Blue
gsettings set org.cinnamon.desktop.interface gtk-theme Apartment-Blue
gsettings set org.cinnamon.desktop.interface icon-theme Apartment-Blue
gsettings set org.gnome.desktop.interface gtk-theme Apartment-Blue
csd-xsettings >evidence/xsettings.log 2>&1 &
sleep 2

for major in 3 4; do
  /usr/bin/python3 tests/load-gtk.py "$major"
done

cinnamon --replace >evidence/cinnamon.log 2>&1 &
cinnamon_pid=$!
trap 'kill "$cinnamon_pid" 2>/dev/null || true' EXIT
for attempt in {1..25}; do
  if xprop -root _NET_SUPPORTING_WM_CHECK | grep -q 'window id'; then
    break
  fi
  if ! kill -0 "$cinnamon_pid"; then
    cat evidence/cinnamon.log
    exit 1
  fi
  sleep 1
done
xprop -root _NET_SUPPORTING_WM_CHECK | grep 'window id'

# The virtual display sets both Cinnamon's scale and GDK_SCALE. Keep Xft
# font DPI from scaling a second time in the GTK test applications.
if [ "$SCALE" = 2 ]; then
  export GDK_DPI_SCALE=0.5
  dbus-update-activation-environment GDK_DPI_SCALE
fi

bash tests/chrome-smoke.sh

nemo --no-desktop "$preview_home" >evidence/nemo.log 2>&1 &
timeout 25 xdotool search --sync --onlyvisible --class nemo windowmove 150 140 windowactivate --sync
sleep 2
import -window root evidence/nemo.png

# Use solid backdrops so the frame is easy to judge at both extremes.
xsetroot -solid '#dddfe2'
sleep .3
import -window root evidence/frame-light.png
xsetroot -solid '#171b21'
sleep .3
import -window root evidence/frame-dark.png
xdotool mousemove 675 565 click 3
sleep 1
import -window root evidence/nemo-context.png
xdotool key Escape mousemove 67 1060
sleep 1
xdotool click 3 mousemove 110 1000
sleep 1
import -window root evidence/taskbar-app-menu.png
xdotool key Escape mousemove 550 1060 click 3
sleep 1
import -window root evidence/panel-context.png
xdotool key Escape

terminal_default=$(gsettings get org.gnome.Terminal.ProfilesList default)
python3 extras/terminal/import-gnome-terminal.py
test "$(gsettings get org.gnome.Terminal.ProfilesList default)" = "$terminal_default"
gnome-terminal --profile='Apartment Blue' --geometry=52x16+180+145 --title='Apartment Blue terminal' -- \
  sh -c 'printf "Apartment Blue\n"; sleep 45' >evidence/terminal.log 2>&1 &
timeout 25 xdotool search --sync --onlyvisible --name 'Apartment Blue terminal' windowactivate --sync
sleep 2
import -window root evidence/terminal.png
xdotool key Super_L
sleep 1
import -window root evidence/menu.png
xdotool key Escape mousemove 1883 1060 click 1
sleep 1
import -window root evidence/calendar.png
xdotool key Escape

# Use Cinnamon's notification service and capture the banner while it is open.
xdotool mousemove 900 650
import -window root evidence/before-notification.png
notify-send -a 'Apartment Blue' -i dialog-information 'Apartment Blue' 'Theme preview'
sleep 1
import -window root evidence/notification.png
if compare -metric AE evidence/before-notification.png evidence/notification.png null: 2>evidence/notification-pixels.txt; then
  echo 'Cinnamon did not show the notification' >&2
  exit 1
fi

python3 libadwaita.py apply --legacy
gsettings set org.gnome.desktop.interface color-scheme prefer-dark
env -u GTK_THEME celluloid >evidence/celluloid.log 2>&1 &
timeout 25 xdotool search --sync --onlyvisible --class '[Cc]elluloid' windowmove 180 140 windowactivate --sync
sleep 2
import -window root evidence/celluloid.png
if grep -Ei 'theme parser error|failed to import' evidence/celluloid.log; then
  exit 1
fi
