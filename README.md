# Caves of Soukka
Finger-tracing game for Pythonista

![Main screen](https://github.com/mikaelho/caves/play_images/main_screen.jpg)

Caves of Soukka is a game where you race friends through a playfield, visiting a set of waypoints in order.

## Play

First you pick a playfield and the colors of the players. Actual racing equals drawing a path with your finger, with the added challenge that the __screen goes black__ when you draw, and you get no indication of whether you have reached a waypoint or not.

Your turn ends when you hit a wall; next round, you continue where you crashed.

Your turn starts when you touch the area indicated bu a black circle.

You win when you reach the last waypoint. Everyone gets an equal amount of turns.

## Create

Creating new playfields is fun. One way is to use the game's built-in editor, where you can just draw with your finger to create the field you want.

The editor supports toggling between digging and filling, changing the background picture, and undos/redos. Waypoints are added by dragging them from the left edge. You can move waypoints around, and delete them by dragging them back to the left edge.

New backgrounds can be added by dropping them in the `backgrounds` folder.

As playfields are just images where transparent pixels represent free space and non-transparent pixels the walls, it is easy to create playfield from existing images, or an image that you have designed in some other editor. The free app [Magic Eraser](https://appsto.re/fi/5Spa7.i) is good for making areas of the picture transparent; then you can save the image as PNG. Put the image in the `playfields` folder, rename it to something descriptive, then open it up in the in-game editor to add waypoints.

This example was created by using the same image as both the playfield and the background - the playfield image just has the accessible areas made transparent.

A nice option (especially for the kids and other artistic people) is to design the playfield on paper. It is easy to take a picture and then follow the above process to turn it into a playable object.


