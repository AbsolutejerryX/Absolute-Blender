bl_info = {
    "name": "Absolute Texture",
    "author": "Absolute Jerry",
    "version": (1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar (N-Panel) > Tool Tab",
    "description": "Instantly locks all current and new images/materials as Fake Users when enabled.",
    "warning": "",
    "doc_url": "",
    "category": "System",
}

import bpy

# 1. Universal layout logic to protect BOTH materials and textures
def enforce_fake_user_everywhere():
    # Loop through and lock all Materials
    for mat in bpy.data.materials:
        if not mat.use_fake_user:
            mat.use_fake_user = True
            
    # Loop through and lock all Textures/Images
    for img in bpy.data.images:
        # Avoid breaking internal system render layouts or viewer nodes
        if img.type in {'RENDER_RESULT', 'COMPOSITOR'}:
            continue
        if not img.use_fake_user:
            img.use_fake_user = True

# 2. Instant-Response Handler (Triggers on any scene or data change)
@bpy.app.handlers.persistent
def perma_fake_user_handler(scene, depsgraph=None):
    # Safely pull the scene from context to read the toggle checkbox state
    ctx_scene = getattr(bpy.context, "scene", None)
    if not ctx_scene and len(bpy.data.scenes) > 0:
        ctx_scene = bpy.data.scenes[0]
        
    if ctx_scene and getattr(ctx_scene, "perma_fake_user_toggle", False):
        enforce_fake_user_everywhere()

# 3. Create the panel in the 3D View Sidebar (N-Panel)
class TEXTURE_PT_PermaFakeUserPanel(bpy.types.Panel):
    bl_label = "Absolute Texture"  
    bl_idname = "TEXTURE_PT_perma_fake_user"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool' 

    def draw(self, context):
        layout = self.layout
        
        scene = None
        if context and hasattr(context, "scene"):
            scene = context.scene
            
        if not scene and len(bpy.data.scenes) > 0:
            scene = bpy.data.scenes[0]
            
        if scene:
            col = layout.column(align=True)
            col.prop(scene, "perma_fake_user_toggle", text="Perma Fake User", toggle=True, icon='FAKE_USER_ON')
        else:
            layout.label(text="Loading Scene data...")

# 4. Safe registration hooks for the Addon Engine
def register():
    # Register the property to the Scene class structure dynamically
    bpy.types.Scene.perma_fake_user_toggle = bpy.props.BoolProperty(
        name="Perma Fake User Mode",
        description="Automatically locks all current and new images/materials as Fake Users when enabled",
        default=False
    )
    
    bpy.utils.register_class(TEXTURE_PT_PermaFakeUserPanel)
    
    # Attach our instant event handler to the dependency graph update stack
    if perma_fake_user_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(perma_fake_user_handler)

def unregister():
    bpy.utils.unregister_class(TEXTURE_PT_PermaFakeUserPanel)
    
    # Clean up event handler stack on exit
    if perma_fake_user_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(perma_fake_user_handler)
        
    if hasattr(bpy.types.Scene, "perma_fake_user_toggle"):
        del bpy.types.Scene.perma_fake_user_toggle

if __name__ == "__main__":
    register()
