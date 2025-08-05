bl_info = {
    "name": "GridIt",
    "author": "Ethan Robins",
    "version": (0, 1, 1),
    "blender": (4, 5, 1),
    "description": "Shape-preserving remeshing/topology tool",
    "category": "Mesh"
}

import bpy

from . import preferences, update
from .tools import grid_by_world

# bl_info = bl_info.bl_info

modules = [preferences, update, grid_by_world]

def register():
    for mod in modules:
        mod.register()
    bpy.app.timers.register(update.check_for_updates, first_interval=3.0)

def unregister():
    for mod in reversed(modules):
        mod.unregister()