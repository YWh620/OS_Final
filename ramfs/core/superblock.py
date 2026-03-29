"""
SuperBlock Implementation - Filesystem Global State

Manages filesystem-wide metadata including quotas, inode allocation,
and mount status.
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from ..types import FileType
from .inode import Inode


@dataclass
class SuperBlock:
    """
    Filesystem superblock - manages global state
    
    Attributes:
        block_size: Size of each page/block (default 4KB)
        max_blocks: Maximum number of blocks (quota limit)
        total_blocks: Current number of blocks used
        inode_counter: Counter for generating unique inode numbers
        root_inode: Root directory inode
        mounted: Current mount status
        mount_path: Mount path
        created_time: When superblock was created
    """
    block_size: int = 4096
    max_blocks: int = 25600  # 100MB default
    total_blocks: int = 0
    inode_counter: int = 0
    root_inode: Optional[Inode] = None
    mounted: bool = False
    mount_path: str = "/mnt"
    created_time: float = field(default_factory=time.time)
    
    def allocate_inode(self, file_type: FileType) -> Inode:
        """Allocate a new inode with unique number"""
        self.inode_counter += 1
        return Inode(
            ino=self.inode_counter,
            file_type=file_type,
            permissions=0o755 if file_type == FileType.DIRECTORY else 0o644
        )
    
    def check_quota(self, blocks_needed: int = 1) -> bool:
        """Check if we have enough space (Quota OK?)"""
        return (self.total_blocks + blocks_needed) <= self.max_blocks
    
    def allocate_blocks(self, count: int = 1) -> bool:
        """Try to allocate blocks from quota"""
        if not self.check_quota(count):
            return False
        self.total_blocks += count
        return True
    
    def free_blocks(self, count: int = 1) -> None:
        """Free blocks back to quota"""
        self.total_blocks = max(0, self.total_blocks - count)
    
    def get_available_blocks(self) -> int:
        """Get number of available blocks"""
        return max(0, self.max_blocks - self.total_blocks)
