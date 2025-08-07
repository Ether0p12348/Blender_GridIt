import bpy

from .manifest import manifest
from .enums import UpdateChannel

def get_addon_prefs():
    wm = bpy.context.window_manager
    return wm.get(f"{manifest.id}_prefs", {})


def set_addon_pref(key, value):
    wm = bpy.context.window_manager
    prefs = wm.get(f"{manifest.id}_prefs", {})
    prefs[key] = value
    wm[f"{manifest.id}_prefs"] = prefs


class GridItPreferences(bpy.types.Panel):
    bl_extension_id = manifest.id
    bl_label = f"{manifest.name} Preferences"
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "extensions"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def register(cls):
        bpy.types.WindowManager.gridit_auto_update = bpy.props.BoolProperty(
            name="Automatic Updates",
            description="Automatically install updates",
            default=True
        )
        bpy.types.WindowManager.gridit_update_channel_sel = bpy.props.EnumProperty(
            name="Update Channel",
            description="Choose which channel to check for updates",
            items=[
                (UpdateChannel.STABLE.value, "Stable", "Only install stable updates"),
                (UpdateChannel.BETA.value, "Beta", "Install beta versions as well"),
                (UpdateChannel.DEV.value, "Dev", "Get all development updates")
            ],
            default=UpdateChannel.STABLE.value
        )

    @classmethod
    def unregister(cls):
        del bpy.types.WindowManager.gridit_auto_update
        del bpy.types.WindowManager.gridit_update_channel_sel

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        about_box = layout.box()
        about_box.label(text=f"About {manifest.name}", icon="INFO")
        about_box.label(text=f"v{manifest.version} ({manifest.type})")
        about_box.separator()
        about_box.label(text="Links:")
        if manifest.website:
            row = about_box.row()
            row.operator("wm.url_open", text="GitHub Repository", icon="URL").url = manifest.website

        options_box = layout.box()
        options_box.enabled = False
        options_box.label(text="Options (Unavailable)", icon="PREFERENCES")
        options_box.prop(wm, "gridit_auto_update")
        options_box.prop(wm, "gridit_update_channel_sel")
        options_box.separator()

        options_box.label(text="Maintenance", icon="TOOL_SETTINGS")
        maint_row = options_box.row()
        maint_row.operator(f"{manifest.id}.check_updates", icon="FILE_SCRIPT")
        maint_row.operator(f"{manifest.id}.manual_reload", icon="FILE_REFRESH")

class GRIDIT_OT_ManualReload(bpy.types.Operator):
    bl_idname = f"{manifest.id}.manual_reload"
    bl_label = f"Reload {manifest.name}"
    bl_description = f"Force reload the {manifest.name} {manifest.type}"

    def execute(self, context):
        from .update import reload_addon
        self.report({'INFO'}, f"{manifest.name} reloading...")
        reload_addon()
        return {'FINISHED'}

class GRIDIT_OT_CheckUpdates(bpy.types.Operator):
    bl_idname = f"{manifest.id}.check_updates"
    bl_label = "Check for Updates"
    bl_description = "Immediately check GitHub for updates (will install if available)"

    def execute(self, context):
        from .update import check_for_updates
        self.report({'INFO'}, f"Checking for updates for {manifest.name}...")
        check_for_updates(True)
        return {'FINISHED'}

classes = (
    GridItPreferences,
    GRIDIT_OT_ManualReload,
    GRIDIT_OT_CheckUpdates
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)