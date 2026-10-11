bl_info = {
    "name": "Absolute Colour",
    "author": "Absolute Jerry",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "location": "Image Editor > Image Menu > Save JPEG with Absolute Colour...",
    "description": "Cross-engine background flattener fully optimized for Blender 3.x/4.x/5.x and UPBGE.",
    "category": "Render",
}

import bpy
import os

def convert_srgb_to_linear(c):
    """Accurate manual standard sRGB to Linear conversion formula across versions"""
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4

class WM_OT_SaveCustomJpeg(bpy.types.Operator):
    """Saves the current view to a JPEG file with a solid, accurate background colour"""
    bl_idname = "wm.save_custom_jpeg"
    bl_label = "Save JPEG with Absolute Colour"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.jpg;*.jpeg", options={'HIDDEN'})

    # Bind property straight onto the operator to force drawing in UPBGE file views
    jpeg_bg_color: bpy.props.FloatVectorProperty(
        name="BG Colour",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        size=3,
        min=0.0, max=1.0
    )

    def execute(self, context):
        scene = context.scene
        
        if not self.filepath:
            self.filepath = os.path.join(bpy.path.abspath("//"), "Untitled.jpg")
        if not self.filepath.lower().endswith(('.jpg', '.jpeg')):
            self.filepath += ".jpg"

        screen_image = None
        if context.space_data and context.space_data.type == 'IMAGE_EDITOR':
            screen_image = context.space_data.image
            
        if not screen_image:
            screen_image = bpy.data.images.get("Render Result")

        if not screen_image:
            self.report({'ERROR'}, "Please render your scene with F12 first!")
            return {'CANCELLED'}

        orig_format = scene.render.image_settings.file_format
        scene.render.image_settings.file_format = 'OPEN_EXR'
        scene.render.image_settings.color_mode = 'RGBA'
        
        temp_dir = bpy.app.tempdir
        temp_path = os.path.join(temp_dir, "blender_raw_linear_buffer.exr")
        
        try:
            screen_image.save_render(filepath=temp_path, scene=scene)
            process_img = bpy.data.images.load(temp_path, check_existing=False)
            pixels = list(process_img.pixels)
            
            # Safe extraction regardless of whether context returns a tuple list or a Color Object
            color_prop = self.jpeg_bg_color
            if hasattr(color_prop, "r"):
                raw_r, raw_g, raw_b = color_prop.r, color_prop.g, color_prop.b
            elif hasattr(color_prop, "__getitem__") or isinstance(color_prop, (list, tuple)):
                raw_r, raw_g, raw_b = color_prop[0], color_prop[1], color_prop[2]
            else:
                raw_r, raw_g, raw_b = color_prop, color_prop, color_prop
            
            bg_r = convert_srgb_to_linear(raw_r)
            bg_g = convert_srgb_to_linear(raw_g)
            bg_b = convert_srgb_to_linear(raw_b)
            
            for idx in range(0, len(pixels), 4):
                r = pixels[idx]
                g = pixels[idx+1]
                b = pixels[idx+2]
                a = pixels[idx+3]
                
                pixels[idx]   = (r * a) + (bg_r * (1.0 - a))
                pixels[idx+1] = (g * a) + (bg_g * (1.0 - a))
                pixels[idx+2] = (b * a) + (bg_b * (1.0 - a))
                pixels[idx+3] = 1.0 
                
            process_img.pixels = pixels
            
            process_img.file_format = 'JPEG'
            process_img.filepath_raw = self.filepath
            process_img.save() 
            
            bpy.data.images.remove(process_img)
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            self.report({'INFO'}, f"Saved cleanly with custom background to: {self.filepath}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Export sequence failed: {str(e)}")
        finally:
            scene.render.image_settings.file_format = orig_format

        return {'FINISHED'}

    def draw(self, context):
        """Draws the options layout safely on the sidebar parameters window"""
        layout = self.layout
        layout.label(text="Absolute Colour Properties:")
        layout.prop(self, "jpeg_bg_color", text="BG Colour")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def draw_image_menu_entry(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("wm.save_custom_jpeg", text="Save JPEG with Absolute Colour...", icon='COLOR')

def register():
    bpy.utils.register_class(WM_OT_SaveCustomJpeg)
    bpy.types.IMAGE_MT_image.append(draw_image_menu_entry)

def unregister():
    bpy.utils.unregister_class(WM_OT_SaveCustomJpeg)
    bpy.types.IMAGE_MT_image.remove(draw_image_menu_entry)

if __name__ == "__main__":
    register()
