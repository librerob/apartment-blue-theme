# Desktop checks

Run these in a test Cinnamon account. Install and select Apartment Blue before opening the apps. Repeat at 100% and 200% scaling.

- Open Nemo in icon and list view. Check the home folders, sidebar, selection, search and a file chooser.
- Compare the terminal's Cinnamon-drawn title bar with a GTK app that draws its own. Hover, press and keyboard-focus the window buttons. Check inactive, maximised and tiled windows and both button placements.
- Right-click the Nemo file pane and a running app in the panel. Open the menu and calendar. Switch workspaces, open the window list and check a notification. Try the panel on each screen edge.
- In Celluloid, check the title buttons, file menu and controls over a playing video. Open a native libadwaita app on Mint in light and dark appearances and check high contrast. Test the optional stylesheet on an upstream GTK 4 session and on a single Flatpak app.
- Check for parse errors in the app's stderr and Cinnamon's Looking Glass log. CSS that parses can still match the wrong widget, so check the result on screen.
