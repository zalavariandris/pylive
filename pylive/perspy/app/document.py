from pathlib import Path
from imgui_bundle import imgui
from PIL.Image import Image
import glm
import json
import base64
from imgui_bundle import portable_file_dialogs as pfd
from enum import IntEnum
from typing import List, Tuple
from struct import pack, unpack

from typing import Literal
import pyperclip


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

class BaseDocument(ABC):
    def __init__(self):
        # if not isinstance(extension, str) or not extension.startswith('.'):
        #     raise ValueError(f"Extension must be a string starting with '.', got: {extension}")
        
        # if not isinstance(magic, bytes):
        #     raise ValueError(f"Magic must be bytes, got: {type(magic).__name__}")
        
        # if len(magic) != 4:
        #     raise ValueError(f"Magic must be 4 bytes long, got length: {len(magic)}")
        
        self._file_path: str|None = None
        # self._version = version
        # self._extension = extension
        # self._magic = magic
        # self._format_description = format_description

    @abstractmethod
    def extension(self)->str:
        return '.prsy'
    
    @abstractmethod
    def name(self)->str:
        return 'perspy'
    
    @abstractmethod
    def magic(self)->bytes:
        """for bytes magic number"""
        return b'prsy'
    
    @abstractmethod
    def version(self)->str:
        return "0.5.0"

    @abstractmethod
    def serialize(self)->bytearray:
        """Serialize the document state to a bytearray containing the complete file format.
        Should be overridden by subclasses.
        """
        return bytearray()
    
    @abstractmethod
    def deserialize(self, file_bytes: bytearray):
        """Deserialize bytearray to restore document state.
        Should be overridden by subclasses.
        """
        pass
    
    def _open_save_dialog(self, title="Save"):
        """Prompt for file location and save document."""
        save_dialog = pfd.save_file(
            title=title, 
            default_path="", 
            filters=[self.name(), self.extension()]
        )
        choosen_filepath = save_dialog.result()
        if not choosen_filepath:
            return  # if no filepath was chosen, abort save
        return choosen_filepath
    
    def save_as(self):
        chosen_filepath = self._open_save_dialog(title="Save Project As...")
        if chosen_filepath:
            self.save(filepath=chosen_filepath)

    def save(self, filepath: str|None=None):
        assert filepath is None or isinstance(filepath, str), f"got:, {filepath}"
        """
        Save the document to a custom file format.
        
        File structure:
        - Magic number (4 bytes): document type identifier
        - Version (4 bytes): format version number
        - Data size (4 bytes): size of the serialized data
        - Data: serialized document state
        """

        # Determine if we need to prompt for filepath
        if filepath is None:
            if self._file_path is None:
                # No existing file and no filepath provided - need to prompt
                filepath = self._open_save_dialog(title="Save Project")
                if not filepath:
                    return  # User cancelled dialog
            else:
                # Use existing file path
                filepath = self._file_path

        if not filepath:
            return
        
        # Ensure the file has the correct extension
        if Path(filepath).suffix != self.extension():
            filepath = str(Path(filepath).with_suffix(self.extension()))

        # Get complete file bytes (serialize already includes header)
        file_bytes = self.serialize()

        # Write all bytes at once
        with open(filepath, 'wb') as f:
            f.write(file_bytes)

        logger.info(f"✓ Saved to {filepath}")
        self._file_path = filepath

    def open(self, filepath: str|None=None):
        """
        Load document state from file.
        """
        if filepath is None:
            """Prompt for file location"""
            open_file_dialog = pfd.open_file(
                title="Open Project", 
                default_path="", 
                filters=[f"{self.name()} files", f"*{self.extension()}"]
            )
            paths = open_file_dialog.result()
            if len(paths) > 0:
                filepath = paths[0]
            else:
                return
        
        # Read entire file into memory
        with open(filepath, 'rb') as f:
            file_bytes = bytearray(f.read())

        self.deserialize(file_bytes)
        
        logger.info(f"✓ Open from {filepath}")
        self._file_path = filepath

    def _construct_header(self, data_size: int) -> bytearray:
        """Construct file header with magic, version, and data size.
        
        Args:
            data_size: Size of the document data in bytes
            
        Returns:
            bytearray: 12-byte header
        """
        magic_bytes = int.from_bytes(self.magic(), byteorder='little')
        version = int(self.version().split('.')[0])  # Use major version
        
        header = bytearray()
        header.extend(pack('<I', magic_bytes))    # 4 bytes: magic number
        header.extend(pack('<I', version))        # 4 bytes: version
        header.extend(pack('<I', data_size))      # 4 bytes: data size
        
        return header
    
    def _parse_header(self, file_bytes: bytearray) -> tuple[bytearray, int]:
        """Parse file header and extract document data.
        
        Args:
            file_bytes: Complete file content as bytearray
            
        Returns:
            tuple: (document_data, offset) where offset points to end of header
            
        Raises:
            ValueError: If header is invalid
        """
        if len(file_bytes) < 12:
            raise ValueError(f"File too small - expected at least 12 bytes, got {len(file_bytes)}")
        
        offset = 0
        
        # Read magic bytes
        magic_bytes = file_bytes[offset:offset+4]
        offset += 4
        
        if magic_bytes != self.magic():
            raise ValueError(f"Not a valid {self.name()} file (got magic: {magic_bytes})")
        
        # Read version
        version = unpack('<I', file_bytes[offset:offset+4])[0]
        offset += 4
        
        expected_version = int(self.version().split('.')[0])  # Use major version
        if version != expected_version:
            raise ValueError(f"Unsupported version: {version}, expected: {expected_version}")
        
        # Read data size
        data_size = unpack('<I', file_bytes[offset:offset+4])[0]
        offset += 4
        
        if len(file_bytes) < offset + data_size:
            raise ValueError(f"File truncated - expected {data_size} bytes of data, got {len(file_bytes) - offset}")
        
        # Extract document data
        document_data = bytearray(file_bytes[offset:offset+data_size])
        
        return document_data, offset + data_size


class PerspyDocument(BaseDocument):
    def __init__(self):
        super().__init__()
        # solver inputs
        # - content image
        self.image_path: str|None = '0a42f3b2-dc40-4f26-bae7-a14eaacc9488-1757x2040.jpg'
        self.content_size = imgui.ImVec2(1757.000000, 2040.000000)

        # - solver params
        self.solver_mode=solver.SolverMode.ThreeVP
        
        self.first_axis=solver.Axis.NegativeX
        self.second_axis=solver.Axis.PositiveY
        self.third_axis=solver.Axis.PositiveZ
        self.fov_degrees=240.0 # only for OneVP mode
        self.quad_mode=False # only for TwoVP mode. is this a ui state?
        self.enable_auto_principal_point=True

        # - control points
        self.origin:imgui.ImVec2 = imgui.ImVec2(609.247009, 577.750366)
        self.principal:imgui.ImVec2 = imgui.ImVec2(1757/2, 2040/2)
        self.first_vanishing_lines: List[Tuple[imgui.ImVec2, imgui.ImVec2]] = [
            (imgui.ImVec2(      1561.62,      1466.54 ), imgui.ImVec2(      281.936,      1872.16 )),
            (imgui.ImVec2(      1008.14,      60.5322 ), imgui.ImVec2(     -37.6624,      900.753 ))
        ]
        self.second_vanishing_lines: List[Tuple[imgui.ImVec2, imgui.ImVec2]] = [
            (imgui.ImVec2(      857.368,      815.351 ), imgui.ImVec2(      1319.06,      1505.22 )),
            (imgui.ImVec2(     -49.4138,      1045.43 ), imgui.ImVec2(       985.78,      1848.83 ))
        ]
        self.third_vanishing_lines: List[Tuple[imgui.ImVec2, imgui.ImVec2]] = [
            (imgui.ImVec2(      260.742,      327.019 ), imgui.ImVec2(     -45.1552,      1919.01 )),
            (imgui.ImVec2(      1454.11,      600.881 ), imgui.ImVec2(      1670.46,      1914.78 ))
        ]

        # reference distance
        self.reference_world_size = 1.0
        self.reference_axis:solver.ReferenceAxis = solver.ReferenceAxis.Screen
        self.reference_distance_offset = 0.0
        self.reference_distance_length =   100.0

    def extension(self)->str:
        return '.prsy'
    
    def name(self)->str:
        return 'perspy'
    
    def magic(self)->bytes:
        """for bytes magic number"""
        return b'prsy'
    
    def version(self)->str:
        return "0.5.0"

    def serialize(self)->bytearray:
        data = {
            'version': self._version,
            'solver_params': {
                "mode": solver.SolverMode(self.solver_mode).name,
                "first_axis": solver.Axis(self.first_axis).name,
                "second_axis": solver.Axis(self.second_axis).name,
                "scene_scale": self.reference_world_size,
                "fov_degrees": self.fov_degrees,
                "quad_mode": self.quad_mode,
                "reference_distance_mode": solver.ReferenceAxis(self.reference_axis).name,
                "reference_distance_segment": [self.reference_distance_offset, self.reference_distance_length]
            },

            'control_points': {
                "origin": self.origin,
                "principal_point": self.principal,
                "first_vanishing_lines": self.first_vanishing_lines,
                "second_vanishing_lines": self.second_vanishing_lines
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

        # Convert document data to JSON
        document_data = json.dumps(data, indent=4, default=json_serializer).encode('utf-8')
        
        # Build complete file: header + document data
        header = self._construct_header(len(document_data))
        
        file_bytes = bytearray()
        file_bytes.extend(header)          # 12 bytes: header
        file_bytes.extend(document_data)   # N bytes: JSON data

        return file_bytes

    def deserialize(self, file_bytes: bytearray):
        """Deserialize complete file format to restore document state."""
        # Parse header and extract document data
        document_data, _ = self._parse_header(file_bytes)
        
        # Convert JSON data to string
        json_text = document_data.decode('utf-8')
        
        # Helper functions for deserialization
        def deserialize_vec2(obj)->imgui.ImVec2:
            """Convert dict to imgui.ImVec2"""
            if isinstance(obj, dict) and 'x' in obj and 'y' in obj:
                return imgui.ImVec2(obj['x'], obj['y'])
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
            self.solver_mode = solver.SolverMode[sp['mode']] if 'mode' in sp else solver.SolverMode.OneVP
            self.first_axis = solver.Axis[sp['first_axis']] if 'first_axis' in sp else solver.Axis.PositiveZ
            self.second_axis = solver.Axis[sp['second_axis']] if 'second_axis' in sp else solver.Axis.PositiveX
            self.reference_world_size = sp.get('scene_scale', 5.0)
            self.fov_degrees = sp.get('fov_degrees', 60.0)
            self.quad_mode = sp.get('quad_mode', False)
        
        # Load control points
        if 'control_points' in data:
            cp = data['control_points']
            
            if 'origin' in cp:
                self.origin = deserialize_vec2(cp['origin'])
            
            if 'principal_point' in cp:
                self.principal = deserialize_vec2(cp['principal_point'])
            
            if 'first_vanishing_lines' in cp:
                self.first_vanishing_lines = [
                    (deserialize_vec2(line[0]), deserialize_vec2(line[1]))
                    for line in cp['first_vanishing_lines']
                ]
            
            if 'second_vanishing_lines' in cp:
                self.second_vanishing_lines = [
                    [deserialize_vec2(line[0]), deserialize_vec2(line[1])]
                    for line in cp['second_vanishing_lines']
                ]
        
        # Load image params
        if 'image_params' in data:
            ip = data['image_params']
            self.image_path = ip.get('path', None)
            width = ip.get('width', 720)
            height = ip.get('height', 576)
            self.content_size = imgui.ImVec2(width, height)

    def as_python_script(self):
        """Serialize document and copy to clipboard as base64 string."""
        from textwrap import dedent
        return dedent(f"""\
            # - content image
            self.image_path: str|None = {self.image_path!r}

            # - solver params
            self.solver_mode=SolverMode.{solver.SolverMode(self.solver_mode).name}
            self.scene_scale={self.reference_world_size}
            self.first_axis=solver.Axis.{solver.Axis(self.first_axis).name}
            self.second_axis=solver.Axis.{solver.Axis(self.second_axis).name}
            self.third_axis=solver.Axis.{solver.Axis(self.third_axis).name}
            self.fov_degrees={self.fov_degrees} # only for OneVP mode
            self.quad_mode={self.quad_mode} # only for TwoVP mode. is this a ui state?
            self.enable_auto_principal_point=True

            # - control points
            self.origin=imgui.{self.origin}
            self.principal_point=self.content_size/2
            self.first_vanishing_lines = [
                (imgui.ImVec2.{self.first_vanishing_lines[0][0]}, imgui.ImVec2.{self.first_vanishing_lines[0][1]}),
                (imgui.ImVec2.{self.first_vanishing_lines[1][0]}, imgui.ImVec2.{self.first_vanishing_lines[1][1]})
            ]
            self.second_vanishing_lines = [
                [imgui.ImVec2.{self.second_vanishing_lines[0][0]}, imgui.ImVec2.{self.second_vanishing_lines[0][1]}],
                [imgui.ImVec2.{self.second_vanishing_lines[1][0]}, imgui.ImVec2.{self.second_vanishing_lines[1][1]}]
            ]
            self.third_vanishing_lines = [
                [imgui.ImVec2.{self.third_vanishing_lines[0][0]}, imgui.ImVec2.{self.third_vanishing_lines[0][1]}],
                [imgui.ImVec2.{self.third_vanishing_lines[1][0]}, imgui.ImVec2.{self.third_vanishing_lines[1][1]}]
            ]
        """)

