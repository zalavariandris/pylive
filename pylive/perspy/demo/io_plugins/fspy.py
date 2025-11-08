# fSpy Blender importer
# Copyright (C) 2018 - Per Gantelius
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
from struct import *
from pathlib import Path

class ParsingError(Exception):
    pass

class CameraParameters:
  def __init__(self, json_dict):
    if json_dict is None:
        raise ParsingError("Trying to import an fSpy project with no camera parameters")
    principal_point_dict = json_dict["principalPoint"]
    self.principal_point = (principal_point_dict["x"], principal_point_dict["y"])
    self.fov_horiz = json_dict["horizontalFieldOfView"]
    self.camera_transfrom = json_dict["cameraTransform"]["rows"]
    self.image_width = json_dict["imageWidth"]
    self.image_height = json_dict["imageHeight"]

class Project:
  def __init__(self, project_path):
    project_file = open(project_path, "rb")

    file_id = unpack('<I', project_file.read(4))[0]
    if 2037412710 != file_id:
        raise ParsingError("Trying to import a file that is not an fSpy project")
    self.project_version = unpack('<I', project_file.read(4))[0]
    if self.project_version != 1:
        raise ParsingError("Unsupported fSpy project file version " + str(self.project_version))

    state_string_size = unpack('<I', project_file.read(4))[0]
    image_buffer_size = unpack('<I', project_file.read(4))[0]

    if image_buffer_size == 0:
        raise ParsingError("Trying to import an fSpy project with no image data")

    project_file.seek(16)
    state = json.loads(project_file.read(state_string_size).decode('utf-8'))
    self.camera_parameters = CameraParameters(state["cameraParameters"])
    calibration_settings = state["calibrationSettingsBase"]
    self.reference_distance_unit = calibration_settings["referenceDistanceUnit"]
    self.image_data = project_file.read(image_buffer_size)
    self.file_name = os.path.basename(project_path)

def export_to_fspy(output_path, state_dict, image_data):
    """
    Create an fspy file from a state dictionary and image data.
    
    Args:
        output_path: Path where the .fspy file will be saved
        state_dict: Dictionary containing the JSON state (camera parameters, calibration settings, etc.)
        image_data: Raw image bytes (can be JPEG, PNG, etc.)
    
    Example:
        state = {
            "globalSettings": {...},
            "calibrationSettingsBase": {...},
            "cameraParameters": {...},
            ...
        }
        with open("image.jpg", "rb") as f:
            image_data = f.read()
        create_fspy_file("output.fspy", state, image_data)
    """
    # Convert state dict to JSON bytes
    state_json = json.dumps(state_dict, separators=(',', ':')).encode('utf-8')
    state_string_size = len(state_json)
    image_buffer_size = len(image_data)
    
    # fSpy magic number (0x79707366 = "fspy" in ASCII)
    file_id = 2037412710
    project_version = 1
    
    with open(output_path, 'wb') as f:
        # Write 16-byte header
        f.write(pack('<I', file_id))              # 4 bytes: file ID
        f.write(pack('<I', project_version))      # 4 bytes: version
        f.write(pack('<I', state_string_size))    # 4 bytes: JSON size
        f.write(pack('<I', image_buffer_size))    # 4 bytes: image size
        
        # Write JSON state
        f.write(state_json)
        
        # Write image data
        f.write(image_data)
    
    print(f"Created fspy file: {output_path}")
    print(f"  JSON size: {state_string_size} bytes")
    print(f"  Image size: {image_buffer_size} bytes")
    print(f"  Total size: {16 + state_string_size + image_buffer_size} bytes")

def import_from_fspy(fspy_path):
    """
    Import an fspy file and return its contents as a dictionary.
    
    Args:
        fspy_path: Path to the .fspy file to read
    
    Returns:
        dict: A dictionary containing:
            - 'state': The complete JSON state dictionary
            - 'image_data': Raw image bytes
            - 'file_name': Base name of the file
            - 'version': fSpy project version
            - 'camera_parameters': Extracted camera parameters dict
            - 'principal_point': Tuple (x, y)
            - 'fov_horizontal': Horizontal field of view
            - 'fov_vertical': Vertical field of view
            - 'camera_transform': 4x4 transformation matrix
            - 'image_width': Image width in pixels
            - 'image_height': Image height in pixels
            - 'reference_distance_unit': Unit for reference distance
    
    Raises:
        ParsingError: If file is not a valid fSpy project
    
    Example:
        data = import_from_fspy("my_project.fspy")
        print(f"FOV: {data['fov_horizontal']}")
        print(f"Camera transform: {data['camera_transform']}")
        
        # Save the extracted image
        with open("extracted_image.jpg", "wb") as f:
            f.write(data['image_data'])
    """
    with open(fspy_path, 'rb') as f:
        # Read header
        file_id = unpack('<I', f.read(4))[0]
        FSPY_MAGIC_NUMBER = int.from_bytes(b'fspy', byteorder='little')  # 2037412710
        if file_id != FSPY_MAGIC_NUMBER:
            raise ParsingError(f"Not a valid fSpy file (got file ID: {file_id})")
        
        version = unpack('<I', f.read(4))[0]
        if version != 1:
            raise ParsingError(f"Unsupported fSpy version: {version}")
        
        state_string_size = unpack('<I', f.read(4))[0]
        image_buffer_size = unpack('<I', f.read(4))[0]
        
        if image_buffer_size == 0:
            raise ParsingError("fSpy project has no image data")
        
        # Read JSON state
        f.seek(16)
        state_json_bytes = f.read(state_string_size)
        state = json.loads(state_json_bytes.decode('utf-8'))
        
        # Read image data
        image_data = f.read(image_buffer_size)
    
    # Extract commonly used fields
    camera_params = state.get("cameraParameters", {})
    principal_point_dict = camera_params.get("principalPoint", {"x": 0, "y": 0})
    calibration_settings = state.get("calibrationSettingsBase", {})
    
    return {
        'state': state,
        'image_data': image_data,
        'file_name': os.path.basename(fspy_path),
        'version': version,
        'camera_parameters': camera_params,
        'principal_point': (principal_point_dict["x"], principal_point_dict["y"]),
        'fov_horizontal': camera_params.get("horizontalFieldOfView", 0),
        'fov_vertical': camera_params.get("verticalFieldOfView", 0),
        'camera_transform': camera_params.get("cameraTransform", {}).get("rows", []),
        'view_transform': camera_params.get("viewTransform", {}).get("rows", []),
        'image_width': camera_params.get("imageWidth", 0),
        'image_height': camera_params.get("imageHeight", 0),
        'reference_distance_unit': calibration_settings.get("referenceDistanceUnit", "Meters"),
        'vanishing_points': camera_params.get("vanishingPoints", []),
        'relative_focal_length': camera_params.get("relativeFocalLength", 0),
    }


if __name__ == "__main__":
    import sys
    
    # Read and display the raw structure
    fspy_path = '/Users/andris/Desktop/fspy demo.fspy'
    import_from_fspy(fspy_path)
    # Demo: Create a new fspy file
    print("=== Creating a new fspy file ===")
    
    # Create a minimal state dictionary
    minimal_state = {
        "globalSettings": {
            "calibrationMode": "TwoVanishingPoints",
            "imageOpacity": 0.5,
            "overlay3DGuide": "None"
        },
        "calibrationSettingsBase": {
            "referenceDistanceAxis": None,
            "referenceDistance": 1.0,
            "referenceDistanceUnit": "Meters",
            "cameraData": {
                "presetId": "custom",
                "customSensorWidth": 36,
                "customSensorHeight": 24,
                "presetData": {
                    "displayName": "Custom",
                    "sensorWidth": 36,
                    "sensorHeight": 24
                }
            },
            "firstVanishingPointAxis": "xNegative",
            "secondVanishingPointAxis": "zNegative"
        },
        "calibrationSettings1VP": {
            "principalPointMode": "Default",
            "upAxis": "yPositive",
            "horizonMode": "Manual",
            "absoluteFocalLength": 50
        },
        "calibrationSettings2VP": {
            "principalPointMode": "Default",
            "quadModeEnabled": True
        },
        "controlPointsStateBase": {
            "principalPoint": {"x": 0.5, "y": 0.5},
            "origin": {"x": 0.5, "y": 0.5},
            "referenceDistanceAnchor": {"x": 0.5, "y": 0.5},
            "referenceDistanceHandleOffsets": [0, 0],
            "firstVanishingPoint": {"lineSegments": []}
        },
        "controlPointsState1VP": {
            "horizon": {"0": {"x": 0.5, "y": 0.5}, "1": {"x": 0.7, "y": 0.5}}
        },
        "controlPointsState2VP": {
            "secondVanishingPoint": {"lineSegments": []},
            "thirdVanishingPoint": {"lineSegments": []}
        },
        "cameraParameters": {
            "principalPoint": {"x": 0, "y": 0},
            "viewTransform": {
                "rows": [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]
            },
            "cameraTransform": {
                "rows": [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]
            },
            "horizontalFieldOfView": 1.0,
            "verticalFieldOfView": 0.75,
            "vanishingPoints": [{"x": 0, "y": 0}, {"x": 0, "y": 0}, {"x": 0, "y": 0}],
            "vanishingPointAxes": ["xNegative", "zNegative", "yNegative"],
            "relativeFocalLength": 2.0,
            "imageWidth": 1920,
            "imageHeight": 1080
        },
        "resultDisplaySettings": {
            "orientationFormat": "AxisAngleDegrees",
            "principalPointFormat": "Absolute",
            "fieldOfViewFormat": "Degrees",
            "displayAbsoluteFocalLength": True
        }
    }
    
    # Reuse the image from the loaded project
    export_to_fspy('/tmp/test_output.fspy', minimal_state, project.image_data)
    
    # Verify we can read it back
    print("\n=== Verifying created file ===")
    test_project = Project('/tmp/test_output.fspy')
    print(f"Successfully loaded created file: {test_project.file_name}")
    print(f"Image dimensions: {test_project.camera_parameters.image_width}x{test_project.camera_parameters.image_height}")
    
    # Demo: Using import_from_fspy (without Project class)
    print("\n=== Using import_from_fspy function ===")
    data = import_from_fspy(fspy_path)
    print(f"File name: {data['file_name']}")
    print(f"Version: {data['version']}")
    print(f"Image dimensions: {data['image_width']}x{data['image_height']}")
    print(f"FOV (horizontal): {data['fov_horizontal']:.4f} radians")
    print(f"FOV (vertical): {data['fov_vertical']:.4f} radians")
    print(f"Principal point: {data['principal_point']}")
    print(f"Reference distance unit: {data['reference_distance_unit']}")
    print(f"Relative focal length: {data['relative_focal_length']}")
    print(f"Camera transform matrix (first row): {data['camera_transform'][0]}")
    print(f"Number of vanishing points: {len(data['vanishing_points'])}")
    print(f"Image data size: {len(data['image_data'])} bytes")


    