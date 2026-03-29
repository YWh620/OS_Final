"""
RamFS Type Definitions and Enums
"""

from enum import Enum
from dataclasses import dataclass, field
import time
from typing import Dict, Optional


class FileType(Enum):
    """Supported file types"""
    FILE = 1
    DIRECTORY = 2


@dataclass
class FileMetadata:
    """File/directory metadata"""
    ino: int
    file_type: FileType
    permissions: int = 0o644
    size: int = 0
    created_time: float = field(default_factory=time.time)
    modified_time: float = field(default_factory=time.time)
    
    def is_dir(self) -> bool:
        return self.file_type == FileType.DIRECTORY
    
    def is_file(self) -> bool:
        return self.file_type == FileType.FILE
