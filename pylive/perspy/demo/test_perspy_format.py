#!/usr/bin/env python3
"""
Test script for the .perspy file format.
Demonstrates creating and reading .perspy files without the full app.
"""

import json
from struct import pack, unpack
from pathlib import Path
from PIL import Image
import io

def create_perspy_file(filepath: str, state_dict: dict, image_path: str = None):
    """
    Create a .perspy file from a state dictionary and optional image.
    
    File structure:
    - Magic number (4 bytes): b'prsp' (perspective spy)
    - Version (4 bytes): version number
    - JSON size (4 bytes): size of the state JSON
    - Image size (4 bytes): size of the image data
    - JSON data: serialized app state
    - Image data: raw PNG bytes (if available)
    """
    # Get JSON state
    state_json = json.dumps(state_dict, indent=4).encode('utf-8')
    state_size = len(state_json)
    
    # Get image data
    image_data = b''
    if image_path and Path(image_path).exists():
        img = Image.open(image_path)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = buffer.getvalue()
    image_size = len(image_data)
    
    # Write file
    magic = int.from_bytes(b'prsp', byteorder='little')  # 'prsp' = perspective spy
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
    
    print(f"✓ Created {filepath}")
    print(f"  Magic: {magic:#010x} ('{magic.to_bytes(4, 'little').decode('ascii')}')")
    print(f"  Version: {version}")
    print(f"  State size: {state_size} bytes")
    print(f"  Image size: {image_size} bytes")
    print(f"  Total size: {16 + state_size + image_size} bytes")


def read_perspy_file(filepath: str):
    """
    Read a .perspy file and return its contents.
    
    Returns:
        dict with keys: 'state', 'image', 'version'
    """
    with open(filepath, 'rb') as f:
        # Read header
        magic_bytes = f.read(4)
        if magic_bytes != b'prsp':
            raise ValueError(f"Not a valid .perspy file (got magic: {magic_bytes})")
        
        version = unpack('<I', f.read(4))[0]
        if version != 1:
            raise ValueError(f"Unsupported version: {version}")
        
        state_size = unpack('<I', f.read(4))[0]
        image_size = unpack('<I', f.read(4))[0]
        
        # Read state JSON
        state_json = f.read(state_size).decode('utf-8')
        state = json.loads(state_json)
        
        # Read image data
        image = None
        if image_size > 0:
            image_data = f.read(image_size)
            image = Image.open(io.BytesIO(image_data))
    
    print(f"✓ Read {filepath}")
    print(f"  Version: {version}")
    print(f"  State: {len(state)} keys")
    if image:
        print(f"  Image: {image.width}x{image.height} ({image.mode})")
    
    return {
        'state': state,
        'image': image,
        'version': version
    }


if __name__ == "__main__":
    # Create a sample .perspy file
    sample_state = {
        "image_path": "/path/to/image.jpg",
        "image_dimensions": [1920, 1080],
        "solver_mode": "TwoVP",
        "origin_pixel": {"x": 960, "y": 540},
        "principal_point_pixel": {"x": 960, "y": 540},
        "first_axis": "PositiveZ",
        "second_axis": "PositiveX",
        "dim_background": True,
        "scene_scale": 5.0,
        "first_vanishing_lines_pixel": [
            [{"x": 100, "y": 200}, {"x": 500, "y": 300}],
            [{"x": 200, "y": 400}, {"x": 600, "y": 500}]
        ],
        "second_vanishing_lines_pixel": [
            [{"x": 300, "y": 200}, {"x": 700, "y": 250}],
            [{"x": 400, "y": 300}, {"x": 800, "y": 350}]
        ],
        "quad_mode": False
    }
    
    # Create test file without image
    test_file = "/tmp/test_project.perspy"
    create_perspy_file(test_file, sample_state)
    
    print("\n" + "="*50 + "\n")
    
    # Read it back
    data = read_perspy_file(test_file)
    
    print("\nState content:")
    print(json.dumps(data['state'], indent=2))
    
    # Inspect the raw file structure
    print("\n" + "="*50 + "\n")
    print("Raw file structure:")
    with open(test_file, 'rb') as f:
        magic = f.read(4)
        version_bytes = f.read(4)
        state_size_bytes = f.read(4)
        image_size_bytes = f.read(4)
        
        print(f"Bytes 0-3 (magic):      {magic} = '{magic.decode('ascii')}'")
        print(f"Bytes 4-7 (version):    {unpack('<I', version_bytes)[0]}")
        print(f"Bytes 8-11 (JSON size): {unpack('<I', state_size_bytes)[0]}")
        print(f"Bytes 12-15 (img size): {unpack('<I', image_size_bytes)[0]}")
        
        # Show first few bytes of JSON
        json_start = f.read(100)
        print(f"\nFirst 100 chars of JSON:")
        print(json_start.decode('utf-8'))
