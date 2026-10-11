# Made by Absolute Jerry

bl_info = {
    "name": "Absolute Deselect J",
    "author": "Absolute Jerry",
    "version": (1, 9),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Hover over Object + Press J",
    "description": "Instantly deselects any object type (Meshes, Lights, Cameras) directly underneath the mouse cursor when pressing J.",
    "category": "3D View",
}

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

class VIEW3D_OT_deselect_hovered_j(bpy.types.Operator):
    bl_idname = "view3d.deselect_hovered_j"
    bl_label = "Deselect Hovered Object with J"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        if context.space_data.type != 'VIEW_3D':
            return {'CANCELLED'}

        region = context.region
        rv3d = context.region_data
        mouse_coord = Vector((event.mouse_region_x, event.mouse_region_y))

        # Define selection distance threshold in screen pixels (handles clicking near centers/gizmos)
        threshold = 40.0 
        closest_obj = None
        min_dist = float('inf')

        # 1. Evaluate selected items to see if mouse is hovering over light/camera pivots
        for obj in context.selected_objects:
            obj_screen_coord = view3d_utils.location_3d_to_region_2d(region, rv3d, obj.matrix_world.translation)
            
            if obj_screen_coord:
                dist = (mouse_coord - obj_screen_coord).length
                if dist < threshold and dist < min_dist:
                    min_dist = dist
                    closest_obj = obj

        # 2. If no pivot was close enough, fallback to standard Raycast for polygon meshes
        if not closest_obj:
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, (mouse_coord.x, mouse_coord.y))
            ray_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, (mouse_coord.x, mouse_coord.y))
            depsgraph = context.evaluated_depsgraph_get()
            hit, location, normal, index, hit_object, matrix = context.scene.ray_cast(depsgraph, ray_origin, ray_vector)
            
            if hit and hit_object:
                closest_obj = hit_object.original if hasattr(hit_object, "original") else hit_object

        # 3. Perform the clean deselection layout update
        if closest_obj and closest_obj.select_get():
            closest_obj.select_set(False)

            if context.view_layer.objects.active == closest_obj:
                context.view_layer.objects.active = None
                
            context.area.tag_redraw()
            return {'FINISHED'}

        return {'PASS_THROUGH'}

# Correctly initialized empty list to hold active custom keymaps
addon_keymaps = []

def register():
    bpy.utils.register_class(VIEW3D_OT_deselect_hovered_j)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            VIEW3D_OT_deselect_hovered_j.bl_idname,
            type='J',
            value='PRESS'
        )
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(VIEW3D_OT_deselect_hovered_j)

if __name__ == "__main__":
    register()
