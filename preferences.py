import bpy

class GridItPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    update_channel: bpy.props.EnumProperty(
        name="Update Channel",
        description="Choose which channel to check for updates",
        items=[
            ('stable', "Stable", "Only install stable updates"),
            ('beta', "Beta", "Install beta versions as well"),
            ('dev', "Developer", "Get all development updates")
        ],
        default='stable'
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "update_channel")

        layout.separator()
        layout.label(text="Maintenance Tools")

        row = layout.row()
        row.operator("gridit.check_updates", icon="FILE_SCRIPT")
        row.operator("gridit.manual_reload", icon="FILE_REFRESH")

class GRIDIT_OT_ManualReload(bpy.types.Operator):
    bl_idname = "gridit.manual_reload"
    bl_label = "Reload GridIt"
    bl_description = "Force reload the GridIt add-on"
    def execute(self, context):
        from . import update
        bpy.app.timers.register(update.reload_addon, first_interval=0.5)
        return {'FINISHED'}

class GRIDIT_OT_CheckUpdates(bpy.types.Operator):
    bl_idname = "gridit.check_updates"
    bl_label = "Check for Updates"
    bl_description = "Immediately check Github for updates (will install if available)"
    def execute(self, context):
        from . import update
        update.check_for_updates()
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