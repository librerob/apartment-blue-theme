#!/usr/bin/env bash
set -eu

frame() {
  read -r x y width < <(xwininfo -id "$window" | awk '
    /Absolute upper-left X:/ { x=$NF }
    /Absolute upper-left Y:/ { y=$NF }
    /^  Width:/ { width=$NF }
    END { print x, y, width }
  ')
  if [ "$kind" = muffin ]; then
    read -r _ right top _ <<< "$(xprop -id "$window" _NET_FRAME_EXTENTS | sed 's/.* = //; s/,//g')"
    y=$((y - top))
  else
    read -r _ right top _ <<< "$(xprop -id "$window" _GTK_FRAME_EXTENTS | sed 's/.* = //; s/,//g')"
    y=$((y + top))
  fi
  right_edge=$((x + width - right))
}

aim() {
  button_x=$((right_edge - (17 + 30 * $1) * SCALE))
  button_y=$((y + 16 * SCALE))
  xdotool mousemove "$button_x" "$button_y"
}

capture() {
  local image="evidence/chrome-$kind$1.png"
  import -window root "$image"
  if [[ "$kind" = muffin || "$kind" = gtk3 ]]; then
    local left=$x
    if [ "$kind" = gtk3 ]; then
      read -r left _ _ _ <<< "$(xprop -id "$window" _GTK_FRAME_EXTENTS | sed 's/.* = //; s/,//g')"
      left=$((x + left))
    fi
    convert "$image" -crop "$((right_edge - left))x$((32 * SCALE))+${left}+${y}" \
      +repage "evidence/titlebar-$kind$1.png"
  fi
}

expect_glyph() {
  local image=$1 expected=$2
  local crop="$((12 * SCALE))x$((12 * SCALE))+$((button_x - 6 * SCALE))+$((button_y - 6 * SCALE))"
  local bright
  bright=$(convert "$image" -crop "$crop" +repage -colorspace gray -threshold 54% -format '%[fx:round(mean*w*h)]' info:)
  if [ "$expected" = visible ]; then
    if [ "$bright" -lt "$SCALE" ]; then
      echo "No glyph in $image at $crop ($bright bright pixels)" >&2
      return 1
    fi
  else
    if [ "$bright" -ne 0 ]; then
      echo "Unexpected glyph in $image at $crop ($bright bright pixels)" >&2
      return 1
    fi
  fi
}

expect_hover_color() {
  local image=$1 color=$2
  local crop="$((12 * SCALE))x$((12 * SCALE))+$((button_x - 6 * SCALE))+$((button_y - 6 * SCALE))"
  local pixels
  # At 1x, a thin stroke can be antialiased across two rows of pixels.
  pixels=$(convert "$image" -crop "$crop" +repage -fuzz 18% \
    -fill black +opaque "$color" -fill white -opaque "$color" \
    -colorspace gray -format '%[fx:round(mean*w*h)]' info:)
  if [ "$pixels" -lt "$SCALE" ]; then
    echo "Missing $color glyph in $image at $crop" >&2
    return 1
  fi
}

wait_for_state() {
  local atom=$1 present=$2
  for _ in {1..40}; do
    if xprop -id "$window" _NET_WM_STATE | grep -q "$atom"; then
      [ "$present" = yes ] && return 0
    else
      [ "$present" = no ] && return 0
    fi
    sleep 0.1
  done
  return 1
}

for kind in muffin gtk3 gtk4 adw; do
  if [ "$kind" = adw ]; then
    python3 libadwaita.py apply --legacy
    env -u GTK_THEME /usr/bin/python3 tests/chrome-probe.py "$kind" >"evidence/chrome-$kind.log" 2>&1 &
  else
    /usr/bin/python3 tests/chrome-probe.py "$kind" >"evidence/chrome-$kind.log" 2>&1 &
  fi
  probe_pid=$!
  echo "Checking $kind at ${SCALE}x"
  trap 'kill "$probe_pid" 2>/dev/null || true' EXIT
  window=$(timeout 20 xdotool search --sync --onlyvisible --name "^Apartment Blue $kind$")
  xdotool windowactivate --sync "$window"
  xdotool mousemove 1700 825
  sleep 1
  xdotool windowmove "$window" 225 150
  sleep 0.6
  frame
  # Give the compositor a pointer update before recording the focused frame.
  xdotool mousemove "$((right_edge - 100 * SCALE))" "$((y + 16 * SCALE))"
  sleep 0.25
  xdotool mousemove 1700 825
  sleep 0.65
  xwininfo -id "$window" >"evidence/chrome-$kind-frame.log"
  xprop -id "$window" _NET_FRAME_EXTENTS _GTK_FRAME_EXTENTS >>"evidence/chrome-$kind-frame.log"
  frame
  capture ""
  for item in '0 close #e39089' '1 maximize #c3a173' '2 minimize #9bb09d'; do
    read -r index control color <<< "$item"
    aim "$index"
    expect_glyph "evidence/chrome-$kind.png" hidden
    sleep 0.35
    capture "-$control-hover"
    expect_hover_color "evidence/chrome-$kind-$control-hover.png" "$color"
    if [ "$kind" = muffin ]; then
      for dx in "$((-12 * SCALE))" "$((12 * SCALE - 1))"; do
        for dy in "$((-12 * SCALE))" "$((12 * SCALE - 1))"; do
          xdotool mousemove "$((button_x + dx))" "$((button_y + dy))"
          sleep .2
          import -window root "evidence/hit-$kind-$control.png"
          expect_hover_color "evidence/hit-$kind-$control.png" "$color"
        done
      done
      echo "$kind hit area $control: 24 × 24 logical px checked"
      aim "$index"
    fi
  done
  xdotool mousedown 1
  sleep .3
  capture "-pressed"
  xdotool mouseup 1
  wait_for_state _NET_WM_STATE_HIDDEN yes
  xdotool windowactivate --sync "$window"
  wait_for_state _NET_WM_STATE_HIDDEN no
  sleep 0.4
  frame
  if [[ "$kind" = muffin || "$kind" = gtk3 ]]; then
    /usr/bin/python3 tests/chrome-probe.py muffin 'Focus target' >evidence/focus-target.log 2>&1 &
    focus_pid=$!
    focus_window=$(timeout 15 xdotool search --sync --onlyvisible --name '^Focus target$')
    xdotool windowmove "$focus_window" 1100 150 windowactivate --sync "$focus_window"
    xdotool mousemove 1700 825
    sleep .5
    capture "-unfocused"
    kill "$focus_pid"
    xdotool windowactivate --sync "$window"
  fi
  aim 1
  xdotool click 1
  wait_for_state _NET_WM_STATE_MAXIMIZED_VERT yes
  sleep 0.6
  frame
  aim 1
  sleep 0.35
  capture "-restore-hover"
  expect_hover_color "evidence/chrome-$kind-restore-hover.png" "#c3a173"
  xdotool click 1
  wait_for_state _NET_WM_STATE_MAXIMIZED_VERT no
  sleep 0.6
  frame
  aim 0
  xdotool click 1
  for _ in {1..40}; do
    if ! kill -0 "$probe_pid" 2>/dev/null; then
      break
    fi
    sleep 0.1
  done
  if kill -0 "$probe_pid" 2>/dev/null; then
    echo "$kind: Close did not exit the probe" >&2
    exit 1
  fi
  cat "evidence/chrome-$kind.log"
  if [ "$kind" != muffin ]; then
    grep -Fx "$kind title bar: 32 logical px" "evidence/chrome-$kind.log"
    for control in close maximize minimize; do
      awk -v control="$control" '
        $1 == "hit" && $2 == "area" && $3 == control && $4 >= 24 && $5 >= 24 { found=1 }
        END { exit !found }
      ' "evidence/chrome-$kind.log" || { echo "$kind $control hit area is smaller than 24 × 24"; exit 1; }
    done
  fi
  if grep -Ei 'theme parser error|failed to import|error loading image' "evidence/chrome-$kind.log"; then
    exit 1
  fi
  wait "$probe_pid"
  trap - EXIT
  echo "$kind: idle and hover screenshots checked, minimize, maximize, restore, and close worked"
done
