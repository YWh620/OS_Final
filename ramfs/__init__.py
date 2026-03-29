"""
RamFS - In-Memory File System Implementation

A pure Python implementation based on Operating Systems Project Topic 12.
"""

from .fs import VirtualFS
from .types import FileType
from .errors import (
    RamFSError,
    FileSystemNotMounted,
    FileNotFound,
    FileExists,
    IsADirectory,
    NotADirectory,
    DirectoryNotEmpty,
    NoSpaceLeft,
    InvalidPath
)

__version__ = "1.0.0"
__all__ = [
    'VirtualFS',
    'FileType',
    'RamFSError',
    'FileSystemNotMounted',
    'FileNotFound',
    'FileExists',
    'IsADirectory',
    'NotADirectory',
    'DirectoryNotEmpty',
    'NoSpaceLeft',
    'InvalidPath'
]
