"""
Inode Implementation - File/Directory Metadata

Represents a file or directory in the filesystem.
Store metadata, pages (data), and children (for directories).
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from ..types import FileType


@dataclass
class Inode:
    """
    Represents file/directory metadata (struct inode in kernel)
    
    Attributes:
        ino: Inode number (unique)
        file_type: FILE or DIRECTORY
        permissions: Unix permissions (e.g., 0o755)
        size: File size in bytes
        created_time: Creation timestamp
        modified_time: Last modification timestamp
        pages: Dictionary of page_index -> page_data (page cache)
        children: For directories, maps filename -> child Inode (dentry cache)
    """
    ino: int
    file_type: FileType
    permissions: int = 0o644
    size: int = 0
    created_time: float = field(default_factory=time.time)
    modified_time: float = field(default_factory=time.time)
    pages: Dict[int, bytes] = field(default_factory=dict)
    children: Dict[str, 'Inode'] = field(default_factory=dict)
    
    def is_dir(self) -> bool:
        """Check if this is a directory"""
        return self.file_type == FileType.DIRECTORY
    
    def is_file(self) -> bool:
        """Check if this is a file"""
        return self.file_type == FileType.FILE
    
    def add_child(self, name: str, child: 'Inode') -> None:
        """Add a child to this directory (d_instantiate)"""
        if not self.is_dir():
            raise ValueError("Cannot add child to a file")
        self.children[name] = child
    
    def remove_child(self, name: str) -> None:
        """Remove a child from this directory (unlink)"""
        if name in self.children:
            del self.children[name]
    
    def get_child(self, name: str) -> Optional['Inode']:
        """Get a child by name"""
        return self.children.get(name)
    
    def list_children(self) -> list:
        """List all children"""
        return list(self.children.items())
    
    def child_count(self) -> int:
        """Count children"""
        return len(self.children)
