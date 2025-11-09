
from imgui_bundle import imgui
from PIL.Image import Image
import glm
import json
import base64
from imgui_bundle import portable_file_dialogs as pfd
from enum import IntEnum
class SolverMode(IntEnum):
    OneVP = 0
    TwoVP = 1

from pylive.perspy import solver

import logging

# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def json_serializer(obj):
    """Custom JSON serializer for glm types."""
    match obj:
        case glm.vec2():
            return {'x': obj.x, 'y': obj.y}
        case glm.vec3():
            return {'x': obj.x, 'y': obj.y, 'z': obj.z}
        case glm.vec4():
            return {'x': obj.x, 'y': obj.y, 'z': obj.z, 'w': obj.w}
        case glm.mat4():
            return {"rows": [
                [obj[col][row] for col in range(4)]
                for row in range(4)
            ]}
        case imgui.ImVec2():
            return {'x': obj.x, 'y': obj.y}
        case imgui.ImVec4():
            return {'x': obj.x, 'y': obj.y, 'z': obj.z, 'w': obj.w}
        case Image():
            image_embed_data = b''
            import io
            buffer = io.BytesIO()
            obj.save(buffer, format='PNG') # Save as PNG to preserve quality, consider using other image formats
            image_embed_data = buffer.getvalue()
            return base64.b64encode(image_embed_data).decode('ascii')
        case _:
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

from abc import ABC, abstractmethod

class Document(ABC):
    def __init__(self):
        self._file_path: str|None = None
        self._is_modified: bool = False

    @abstractmethod
    def serialize(self)->str:
        """Serialize the document state to a JSON string.
        Should be overridden by subclasses.
        """
        return "{}"
    
    @abstractmethod
    def deserialize(self, json_text: str):
        """Deserialize JSON text to restore document state.
        Should be overridden by subclasses.
        """
        pass

    def __setattr__(self, name:str, value):
        """setattr is called whenever an attribute is set on the instance.
        """
        super().__setattr__(name, value)
        if name != '_is_modified':
            object.__setattr__(self, '_is_modified', True)

    def save(self, filepath: str|None=None):
        assert filepath is None or isinstance(filepath, str), f"got:, {filepath}"
        """
        Save the app state to a custom .perspy file format.
        
        File structure:
        - Magic number (4 bytes): b'prsp' (perspective spy)
        - Version (4 bytes): version number
        - JSON size (4 bytes): size of the state JSON
        - Image size (4 bytes): size of the image data
        - JSON data: serialized app state
        - Image data: raw image bytes (if available)
        """

        DoSaveAs = self._file_path != filepath

        if DoSaveAs:
            ...

        if not self._file_path or filepath:
            """Prompt for file location"""
            save_dialog = pfd.save_file(
                title="Save Project As", 
                default_path="", 
                filters=["perspy files", "(*.perspy)"]
            )
            choosen_filepath = save_dialog.result()[0] if save_dialog.result() else None
            if not choosen_filepath:
                return # if no filepath was chosen, abort save
            filepath = choosen_filepath
        elif self._file_path:
            filepath = self._file_path

        if not filepath:
            return

        if filepath is None:
            """Prompt for file location"""
            save_dialog = pfd.save_file(
                title="Save Project As", 
                default_path="", 
                filters=["perspy files", "(*.perspy)"]
            )
            if path:=save_dialog.result():
                filepath = path
            self.file_path = filepath

        import json
        from struct import pack
        
        # Get JSON state
        state_json = self.doc.serialize().encode('utf-8')
        state_size = len(state_json)
        
        # Get image data
        image_data = b''
        if self.doc.image is not None:
            import io
            buffer = io.BytesIO()
            # Save as PNG to preserve quality
            self.doc.image.save(buffer, format='PNG')
            image_data = buffer.getvalue()
        image_size = len(image_data)
        
        # Write file
        magic = int.from_bytes(b'prsy', byteorder='little')  # 'prsy'
        version = 1
        
        with open(filepath, 'wb') as f:
            # Write header (16 bytes)
            f.write(pack('<I', magic))        # 4 bytes: magic number
            f.write(pack('<I', version))      # 4 bytes: version
            f.write(pack('<I', state_size))   # 4 bytes: JSON size
            f.write(pack('<I', image_size))   # 4 bytes: image size
            
            # Write data
            f.write(state_json)
            if image_data:
                f.write(image_data)
        
        logger.info(f"✓ Saved to {filepath}")
        logger.info(f"  State size: {state_size} bytes, Image size: {image_size} bytes")

    def open(self, filepath: str|None=None):
        """
        Load app state from a .perspy file.
        """
        import json
        from struct import unpack
        import io

        if filepath is None:
            """Prompt for file location"""
            open_file_dialog = pfd.open_file(
                title="Open Project", 
                default_path="", 
                filters=["perspy files", "(*.perspy)"]
            )
            paths = open_file_dialog.result()
            if len(paths) > 0:
                filepath = paths[0]
            else:
                return
        
        with open(filepath, 'rb') as f:
            # Read header
            magic_bytes = f.read(4)
            if magic_bytes != b'prsy':
                raise ValueError(f"Not a valid .perspy file (got magic: {magic_bytes})")
            
            version = unpack('<I', f.read(4))[0]
            if version != 1:
                raise ValueError(f"Unsupported version: {version}")
            
            state_size = unpack('<I', f.read(4))[0]
            image_size = unpack('<I', f.read(4))[0]
            
            # Read state JSON
            state_json = f.read(state_size).decode('utf-8')
            
            # Read image data
            image_data = None
            if image_size > 0:
                image_data = f.read(image_size)
        
        # Use deserialize to restore state from JSON
        self.deserialize(state_json)
        
        # Load image
        if image_data:
            import io
            self.image = Image.open(io.BytesIO(image_data))
            self.content_size = imgui.ImVec2(float(self.image.width), float(self.image.height))

            
            logger.info(f"✓ Loaded from {filepath}")
            logger.info(f"  Image: {self.image.width}x{self.image.height}")
        else:
            logger.warning("No image data in file")

        self._is_modified = False
    
class PerspyDocument(Document):
    def __init__(self):
        super().__init__()
        # solver inputs
        # - content image
        self.image_path: str|None = None
        self.content_size = imgui.ImVec2(1280,720)
        self.image: Image = None

        # - solver params
        self.solver_mode=SolverMode.OneVP
        self.scene_scale=5.0
        self.first_axis=solver.Axis.PositiveZ
        self.second_axis=solver.Axis.PositiveX
        self.fov_degrees=60.0 # only for OneVP mode
        self.quad_mode=False # only for TwoVP mode. is this a ui state?

        # - control points
        self.origin_pixel=self.content_size/2
        self.principal_point_pixel=self.content_size/2
        self.first_vanishing_lines_pixel = [
            (glm.vec2(296, 417), glm.vec2(633, 291)),
            (glm.vec2(654, 660), glm.vec2(826, 344))
        ]
        self.second_vanishing_lines_pixel = [
            [glm.vec2(381, 363), glm.vec2(884, 451)],
            [glm.vec2(511, 311), glm.vec2(879, 356)]
        ]

    def serialize(self)->str:
        # _, quat, _, _, _ = solver.decompose(self.camera.transform)
        # euler = solver.extract_euler(self.camera.transform, order=self.current_euler_order)

        data = {
            'version': '0.5.0',
            'solver_params': {
                "mode": SolverMode(self.solver_mode).name,
                "first_axis": solver.Axis(self.first_axis).name,
                "second_axis": solver.Axis(self.second_axis).name,
                "scene_scale": self.scene_scale,
                "fov_degrees": 60.0,
                "quad_mode": False
            },

            'control_points': {
                "origin": self.origin_pixel,
                "principal_point": self.principal_point_pixel,
                "first_vanishing_lines": self.first_vanishing_lines_pixel,
                "second_vanishing_lines": self.second_vanishing_lines_pixel
            },

            'image_params': {
                "path": self.image_path,
                "width": int(self.content_size.x),
                "height": int(self.content_size.y)
            },

            # 'results': {
            #     "camera": {
            #         "view": self.camera.viewMatrix(),
            #         "projection": self.camera.projectionMatrix(),
            #         "fovy_degrees": self.camera.fovy,
            #         "position": self.camera.getPosition(),
            #         "rotation_euler": {"x": euler[0], "y": euler[1], "z": euler[2], "order": solver.EulerOrder(self.current_euler_order).name},
            #         "rotation_quaternion": {"x": quat.x, "y": quat.y, "z": quat.z, "w": quat.w}
            #     },
            #     "vanishing_points": {
            #         "first": self.first_vanishing_point_pixel,
            #         "second": self.second_vanishing_point_pixel
            #     }
            # },

            # 'guides_params': {
            #     "show_grid": self.view_grid,
            #     "show_horizon": self.view_horizon
            # },

            # 'ui_state': {
            #     "dim_background": self.dim_background,
            #     "windows": {
            #         "show_data": self.show_data_window,
            #         "show_style_editor": self.show_styleeditor_window
            #     }
            # }
        }

        return json.dumps(data, indent=4, default=json_serializer)

    def deserialize(self, json_text: str):
        """Deserialize JSON text to restore document state."""
        
        def deserialize_vec2(obj):
            """Convert dict to glm.vec2"""
            if isinstance(obj, dict) and 'x' in obj and 'y' in obj:
                return glm.vec2(obj['x'], obj['y'])
            return obj
        
        def deserialize_imgui_vec2(obj):
            """Convert dict to imgui.ImVec2"""
            if isinstance(obj, dict) and 'x' in obj and 'y' in obj:
                return imgui.ImVec2(obj['x'], obj['y'])
            return obj
        
        data:dict = json.loads(json_text)
        
        # Load solver params
        if 'solver_params' in data:
            sp = data['solver_params']
            self.solver_mode = SolverMode[sp['mode']] if 'mode' in sp else SolverMode.OneVP
            self.first_axis = solver.Axis[sp['first_axis']] if 'first_axis' in sp else solver.Axis.PositiveZ
            self.second_axis = solver.Axis[sp['second_axis']] if 'second_axis' in sp else solver.Axis.PositiveX
            self.scene_scale = sp.get('scene_scale', 5.0)
            self.fov_degrees = sp.get('fov_degrees', 60.0)
            self.quad_mode = sp.get('quad_mode', False)
        
        # Load control points
        if 'control_points' in data:
            cp = data['control_points']
            
            if 'origin' in cp:
                self.origin_pixel = deserialize_vec2(cp['origin'])
            
            if 'principal_point' in cp:
                self.principal_point_pixel = deserialize_vec2(cp['principal_point'])
            
            if 'first_vanishing_lines' in cp:
                self.first_vanishing_lines_pixel = [
                    (deserialize_vec2(line[0]), deserialize_vec2(line[1]))
                    for line in cp['first_vanishing_lines']
                ]
            
            if 'second_vanishing_lines' in cp:
                self.second_vanishing_lines_pixel = [
                    [deserialize_vec2(line[0]), deserialize_vec2(line[1])]
                    for line in cp['second_vanishing_lines']
                ]
        
        # Load image params
        if 'image_params' in data:
            ip = data['image_params']
            self.image_path = ip.get('path', None)
            width = ip.get('width', 1280)
            height = ip.get('height', 720)
            self.content_size = imgui.ImVec2(width, height)
        
        # Note: The actual image data is loaded separately in the open() method
        # of PerspyApp, not here
    