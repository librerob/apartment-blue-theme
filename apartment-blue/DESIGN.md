# Apartment Blue design

| Token | Proposed | 0.5.2 |
| --- | --- | --- |
| Window | `#242628` | `#202830` |
| Panel | `#292C30` | `#333436` to `#202123` |
| Raised | `#303337` | `#27292C` in popovers, `#202830` in notifications |
| Sunken | `#1C1E21` | `#171E25` |
| Text | `#E3E6E9` | `#E0E6EB` |
| Muted text | `#ADB4BD` | `#A6B4C2` |
| Blue accent | `#9BBFE0`, with `#3D5770` for fills | `#8BB6DC` focus and `#345471` fills |
| Outline | `#50555B` | Several dark outlines, including `#111214` |

Reserve blue for selection, focus, progress, and switches. Use shades of graphite to distinguish adjacent surfaces. Keep 1 px outlines on inputs, menus, popovers, and focus states.

Use 6 px corners for controls and selections, and 10 px for windows and floating surfaces. These replace the usual 3 px and 4 px corners. Use 4, 8, 12, 16, and 24 logical px for spacing, with 8 px menu row padding and 16 px around notification content. The 0.5.2 styles use a mix of inherited spacing and local values.

Title controls use a flat circle within the existing 24 px target. A quiet fill marks rest, and a thin glyph marks hover and press.
