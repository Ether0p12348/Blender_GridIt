import bpy
from .bl_info import bl_info, update_channel
from .enums import UpdateChannel

class GridItPreferences(bpy.types.AddonPreferences):
    bl_idname = "gridit"

    update_channel_sel: bpy.props.EnumProperty(
        name="Update Channel",
        description="Choose which channel to check for updates",
        items=[
            ('stable', "Stable", "Only install stable updates"),
            ('beta', "Beta", "Install beta versions as well"),
            ('dev', "Developer", "Get all development updates")
        ],
        default='stable'
    )

    auto_update: bpy.props.BoolProperty(
        name="Automatic Updates",
        description="Automatically install updates",
        default=True
    )

    def draw(self, context):
        layout = self.layout

        v_row = layout.row() # Not getting drawn
        v_row.label(text=f"GridIt Version: v{'.'.join(map(str, bl_info['version']))}-{str(update_channel.value)}") # Not getting drawn

        layout.separator() # Not getting drawn
        layout.label(text="Updates") # Not getting drawn
        up_row = layout.row()
        up_row.prop(self, "auto_update") # Not getting drawn
        up_row.prop(self, "update_channel_sel")

        layout.separator()
        layout.label(text="Maintenance")
        maint_row = layout.row()
        maint_row.operator("gridit.check_updates", icon="FILE_SCRIPT")
        maint_row.operator("gridit.manual_reload", icon="FILE_REFRESH")

class GRIDIT_OT_ManualReload(bpy.types.Operator):
    bl_idname = "gridit.manual_reload"
    bl_label = "Reload GridIt"
    bl_description = "Force reload the GridIt add-on"
    def execute(self, context):
        from . import update
        update.reload_addon()
        self.report({'INFO'}, "GridIt reloaded")
        return {'FINISHED'}

class GRIDIT_OT_CheckUpdates(bpy.types.Operator):
    bl_idname = "gridit.check_updates"
    bl_label = "Check for Updates"
    bl_description = "Immediately check Github for updates (will install if available)"
    def execute(self, context):
        from . import update
        update.check_for_updates(True)
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