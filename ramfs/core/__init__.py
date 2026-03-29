"""
RamFS Core Components

Inode, SuperBlock, and related structures.
"""

from .inode import Inode
from .superblock import SuperBlock

__all__ = ['Inode', 'SuperBlock']
