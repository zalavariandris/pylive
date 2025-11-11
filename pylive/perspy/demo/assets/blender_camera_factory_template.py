import bpy
import mathutils
import math
from typing import Literal

def create_camera(
    camera_name: str="PerspyCam", 
    fov: float=60.0, 
    transform: tuple = ((1.0, 0.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0, 0.0),
                        (0.0, 0.0, 1.0, 0.0),
                        (0.0, 0.0, 0.0, 1.0)),
    mode: Literal['NEW', 'REPLACE', 'UPDATE'] = 'UPDATE'
) -> bpy.types.Object:
    """
    Create or update a camera with specified FOV and transformation.
    
    Args:
        camera_name (str): Name for the camera object
        fov (float): Field of view in radians
        transform (tuple): 4x4 transformation matrix (row-major)
        mode (str): 'NEW' - always create new camera
                    'REPLACE' - delete existing and create new
                    'UPDATE' - update existing or create if not found (preserves links)
    
    Returns:
        bpy.types.Object: The camera object
    
    Raises:
        ValueError: If existing object with camera_name is not a camera type
    """
    
    existing_object = bpy.data.objects.get(camera_name)
    
    # ============================================================================
    # Handle different modes
    # ============================================================================
    match mode:
        case 'UPDATE' if existing_object:
            # Update existing camera (preserves links, keyframes, etc.)
            if existing_object.type != 'CAMERA':
                raise ValueError(f"Object '{camera_name}' exists but is not a camera (type: {existing_object.type})")
            cam_object = existing_object
            cam_data = cam_object.data
        case 'REPLACE' if existing_object:
            # Delete existing and create new
            bpy.data.objects.remove(existing_object, do_unlink=True)
            cam_data = bpy.data.cameras.new(name=camera_name)
            cam_object = bpy.data.objects.new(camera_name, cam_data)
            bpy.context.collection.objects.link(cam_object)
        case _:
            # All other cases: create new camera
            # - NEW mode (regardless of existing_object)
            # - UPDATE/REPLACE when no existing object
            cam_data = bpy.data.cameras.new(name=camera_name)
            cam_object = bpy.data.objects.new(camera_name, cam_data)
            bpy.context.collection.objects.link(cam_object)
    
    # ============================================================================
    # Apply camera parameters (for all modes)
    # ============================================================================
    
    # Set FOV
    cam_data.lens_unit = 'FOV'
    cam_data.angle = fov
    
    # Set sensor size (35mm equivalent)
    cam_data.sensor_width = 36.0
    cam_data.sensor_height = 24.0
    
    # Apply transformation matrix
    cam_object.matrix_world = mathutils.Matrix(transform)
    
    return cam_object


if __name__ == "__main__":
    # Create or update camera
    camera = create_camera(
        CAMERA_NAME, 
        CAMERA_FOV, 
        CAMERA_TRANSFORM, 
        mode='UPDATE'
    )
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    # Select the camera
    bpy.ops.object.select_all(action='DESELECT')
    camera.select_set(True)
    bpy.context.view_layer.objects.active = camera
    
    print(f"✓ Camera '{camera.name}' ready")
    print(f"  FOV: {math.degrees(camera.data.angle):.2f}°")
    print(f"  Position: {camera.location}")