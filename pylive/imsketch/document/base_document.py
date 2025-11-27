from abc import ABC, abstractmethod
from imgui_bundle import portable_file_dialogs as pfd
from pathlib import Path
from struct import pack, unpack

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseDocument(ABC):
    def __init__(self):
        self._file_path: str|None = None

        # validate parameters
        if not isinstance(self.extension(), str) or not self.extension().startswith('.'):
            raise ValueError(f"Extension must be a string starting with '.', got: {self.extension()}")
        
        if not isinstance(self.magic(), bytes):
            raise ValueError(f"Magic must be bytes, got: {type(self.magic()).__name__}")
        
        if len(self.magic()) != 4:
            raise ValueError(f"Magic must be 4 bytes long, got length: {len(self.magic())}")
        
        if not isinstance(self.version(), str):
            raise ValueError(f"Version must be a string, got: {type(self.version()).__name__}")
    
    def open(self, filepath: str|None=None):
        """
        Load document state from file.
        """
        if filepath is None:
            """Prompt for file location"""
            open_file_dialog = pfd.open_file(
                title="Open Project", 
                default_path="", 
                filters=[f"{self._format_description} files", f"*{self._extension}"]
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
        if Path(filepath).suffix != self._extension:
            filepath = str(Path(filepath).with_suffix(self._extension))

        # Get complete file bytes (serialize already includes header)
        file_bytes = self.serialize()

        # Write all bytes at once
        with open(filepath, 'wb') as f:
            f.write(file_bytes)

        logger.info(f"✓ Saved to {filepath}")
        self._file_path = filepath

    def close(self):
        """Close the document and clear state."""
        self._file_path = None

    @abstractmethod
    def extension(self)->str:
        """Return the file extension for this document type."""
    
    @abstractmethod
    def magic(self)->bytes:
        """Return the magic bytes for this document type."""
    
    @abstractmethod
    def version(self)->str:
        """Return the version string for this document type.
        eg: "0.1.1"
        """
    
    @abstractmethod
    def name(self)->str:
        """
        Return the name of this document type.
        used in the UI and file dialogs.
        """
        return 'perspy'

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
            filters=[self._format_description, self._extension]
        )
        choosen_filepath = save_dialog.result()
        if not choosen_filepath:
            return  # if no filepath was chosen, abort save
        return choosen_filepath
    
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
