# geometric-inklines
Blender 3d 2.80 addon. Creates and administrates a combo of modifiers, vertex groups and materialas (TO DO) to generate geometric inverted hull outlines, and bevel based inner lines to objects, that work in realtime.

## INSTALL
This addon works inside Blender 3D 2.80.
You need only OutlineGen.py
Go to Edit -> Preferences -> Add-ons -> Install and search for the file.

## USAGE
You need to have at least 2 materials in your object: the main material/s and the outline material. The outline material should be last in the material slots.
You can enable or disable all the features individually

### Variable thickness map setup
To have a variable thickness outline you have to set up a thickness map. You can do it in two ways.
1. Select just the object and press GENERATE THICKNESS
2. Select a reference light, and then your object

