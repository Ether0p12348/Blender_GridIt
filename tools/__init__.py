from . import grid_by_world

modules = [grid_by_world]

def register():
    for mod in modules:
        mod.register()

def unregister():
    for mod in modules:
        mod.unregister()