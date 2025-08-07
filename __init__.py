import bpy

from . import preferences, update
from . import tools

modules = [preferences, update, tools]

def register():
    for mod in modules:
        if hasattr(mod, "register"):
            mod.register()
    bpy.app.timers.register(update.check_for_updates, first_interval=3.0)

def unregister():
    for mod in modules:
        if hasattr(mod, "unregister"):
            mod.unregister()