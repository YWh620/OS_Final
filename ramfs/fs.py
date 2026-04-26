"""
VirtualFS - Main Filesystem Implementation

High-level filesystem operations similar to VFS layer in Linux kernel.
"""

import base64
import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .types import FileType
from .errors import (
    FileSystemNotMounted, FileNotFound, FileExists,
    IsADirectory, NotADirectory, DirectoryNotEmpty, NoSpaceLeft
)
from .core import Inode, SuperBlock


class VirtualFS:
    """
    Main filesystem interface providing high-level operations.
    
    Similar to VFS in Linux kernel. Provides operations like:
    - mount/umount: lifecycle
    - touch/mkdir: create files and directories
    - read/write/append: file I/O
    - ls: list directories
    - rm/rmdir: delete files and directories
    - stat: get metadata
    - save/load: persistence
    """
    
    def __init__(self, block_size: int = 4096, max_size_mb: int = 100):
        """
        Initialize RamFS filesystem.
        
        Args:
            block_size: Size of each page (default 4KB)
            max_size_mb: Maximum size in MB for quota
        """
        self.block_size = block_size
        self.max_blocks = (max_size_mb * 1024 * 1024) // block_size
        self.superblock = SuperBlock(
            block_size=block_size,
            max_blocks=self.max_blocks
        )
        self.path_cache: Dict[str, Inode] = {}
    
    def mount(self, mount_path: str = "/mnt") -> bool:
        """
        Mount filesystem (fill_super + mount).
        
        Steps:
        1. Setup Superblock
        2. Allocate Root Inode
        3. Allocate Root Dentry
        """
        if self.superblock.mounted:
            raise RuntimeError("Filesystem already mounted")
        
        try:
            self.superblock.mount_path = mount_path
            
            # Allocate Root Inode & Dentry
            root = self.superblock.allocate_inode(FileType.DIRECTORY)
            root.permissions = 0o755
            root.size = 0
            
            self.superblock.root_inode = root
            self.superblock.mounted = True
            self.path_cache['/'] = root
            
            return True
        except Exception as e:
            print(f"Mount failed: {e}")
            return False
    
    def umount(self) -> bool:
        """Unmount filesystem"""
        if not self.superblock.mounted:
            raise RuntimeError("Filesystem not mounted")
        
        self.superblock.mounted = False
        self.path_cache.clear()
        return True
    
    def _check_mounted(self) -> None:
        """Check if filesystem is mounted"""
        if not self.superblock.mounted:
            raise FileSystemNotMounted("Filesystem not mounted")
    
    def _resolve_path(self, path: str) -> Tuple[Optional[Inode], str]:
        """
        Resolve path to parent inode and filename.
        
        Example:
            "/dir/file.txt" -> (dir_inode, "file.txt")
            "/" -> (root, "/")
        """
        self._check_mounted()
        
        path = path.strip()
        if path == '/':
            return self.superblock.root_inode, '/'
        
        # Split path into components
        parts = [p for p in path.split('/') if p]
        
        # Traverse to parent
        current = self.superblock.root_inode
        for part in parts[:-1]:
            if part not in current.children:
                return None, part
            child = current.children[part]
            if not child.is_dir():
                return None, part
            current = child
        
        filename = parts[-1] if parts else ''
        return current, filename
    
    def _get_inode(self, path: str) -> Optional[Inode]:
        """Get inode by path"""
        if path == '/':
            return self.superblock.root_inode
        
        parent, filename = self._resolve_path(path)
        if parent is None:
            return None
        return parent.get_child(filename)
    
    def touch(self, path: str) -> bool:
        """Create an empty file"""
        try:
            parent, filename = self._resolve_path(path)
            if parent is None:
                raise FileNotFound(f"Parent directory not found: {path}")
            
            if filename in parent.children:
                raise FileExists(f"File already exists: {path}")
            
            # Check quota
            if not self.superblock.check_quota(1):
                raise NoSpaceLeft("ENOSPC: No space left on device")
            
            # Allocate new inode
            new_inode = self.superblock.allocate_inode(FileType.FILE)
            new_inode.permissions = 0o644
            
            # Add to parent (d_instantiate)
            parent.add_child(filename, new_inode)
            
            return True
        except Exception as e:
            print(f"Error creating file: {e}")
            return False
    
    def mkdir(self, path: str, permissions: int = 0o755) -> bool:
        """Create a directory"""
        try:
            parent, dirname = self._resolve_path(path)
            if parent is None:
                raise FileNotFound(f"Parent directory not found: {path}")
            
            if dirname in parent.children:
                raise FileExists(f"Directory already exists: {path}")
            
            # Check quota
            if not self.superblock.check_quota(1):
                raise NoSpaceLeft("ENOSPC: No space left on device")
            
            # Allocate directory inode
            new_inode = self.superblock.allocate_inode(FileType.DIRECTORY)
            new_inode.permissions = permissions
            
            # Add to parent
            parent.add_child(dirname, new_inode)
            
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    
    def write(self, path: str, data: str, mode: str = 'w') -> bool:
        """
        Write to file using page cache.
        
        Flow:
        - Grab page (allocate if needed)
        - Copy data
        - Mark dirty (but don't flush)
        """
        try:
            inode = self._get_inode(path)
            if inode is None:
                raise FileNotFound(f"File not found: {path}")
            
            if not inode.is_file():
                raise IsADirectory(f"Not a file: {path}")
            
            data_bytes = data.encode('utf-8')
            
            if mode == 'w':
                # Overwrite: clear existing pages
                old_size = inode.size
                blocks_freed = (old_size + self.block_size - 1) // self.block_size
                if blocks_freed > 0:
                    self.superblock.free_blocks(blocks_freed)
                
                inode.pages.clear()
                inode.size = 0
            
            # Write data using page cache
            bytes_written = 0
            page_index = inode.size // self.block_size
            offset_in_page = inode.size % self.block_size
            
            for chunk_start in range(0, len(data_bytes), self.block_size):
                chunk = data_bytes[chunk_start:chunk_start + self.block_size]
                
                if page_index not in inode.pages:
                    # Allocate new page
                    if not self.superblock.allocate_blocks(1):
                        raise NoSpaceLeft("ENOSPC: No space left on device")
                    inode.pages[page_index] = chunk
                else:
                    inode.pages[page_index] = chunk
                
                bytes_written += len(chunk)
                page_index += 1
                offset_in_page = 0
            
            inode.size += bytes_written
            inode.modified_time = time.time()
            
            return True
        except Exception as e:
            print(f"Error writing to file: {e}")
            return False
    
    def append(self, path: str, data: str) -> bool:
        """Append to file"""
        try:
            inode = self._get_inode(path)
            if inode is None:
                # File doesn't exist, create it
                if not self.touch(path):
                    return False
                inode = self._get_inode(path)
            
            if not inode.is_file():
                raise IsADirectory(f"Not a file: {path}")
            
            data_bytes = data.encode('utf-8')
            page_index = inode.size // self.block_size
            
            for chunk_start in range(0, len(data_bytes), self.block_size):
                chunk = data_bytes[chunk_start:chunk_start + self.block_size]
                
                if page_index not in inode.pages:
                    if not self.superblock.allocate_blocks(1):
                        raise NoSpaceLeft("ENOSPC: No space left on device")
                    inode.pages[page_index] = chunk
                else:
                    inode.pages[page_index] += chunk
                
                page_index += 1
            
            inode.size += len(data_bytes)
            inode.modified_time = time.time()
            
            return True
        except Exception as e:
            print(f"Error appending to file: {e}")
            return False
    
    def read(self, path: str) -> Optional[str]:
        """Read file content from page cache"""
        try:
            inode = self._get_inode(path)
            if inode is None:
                raise FileNotFound(f"File not found: {path}")
            
            if not inode.is_file():
                raise IsADirectory(f"Not a file: {path}")
            
            # Read from page cache
            data_bytes = b''
            for page_index in sorted(inode.pages.keys()):
                data_bytes += inode.pages[page_index]
            
            return data_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def ls(self, path: str = '/') -> Optional[List[Dict]]:
        """List directory contents"""
        try:
            inode = self._get_inode(path) if path != '/' else self.superblock.root_inode
            if inode is None:
                raise FileNotFound(f"Directory not found: {path}")
            
            if not inode.is_dir():
                raise NotADirectory(f"Not a directory: {path}")
            
            # List children from dentry cache
            entries = []
            for name, child in inode.children.items():
                entries.append({
                    'name': name,
                    'type': 'dir' if child.is_dir() else 'file',
                    'size': child.size,
                    'permissions': oct(child.permissions),
                    'inode': child.ino,
                    'modified': datetime.fromtimestamp(child.modified_time).isoformat()
                })
            
            return sorted(entries, key=lambda x: x['name'])
        except Exception as e:
            print(f"Error listing directory: {e}")
            return None
    
    def rm(self, path: str) -> bool:
        """Remove a file"""
        try:
            parent, filename = self._resolve_path(path)
            if parent is None:
                raise FileNotFound(f"Parent directory not found: {path}")
            
            child = parent.get_child(filename)
            if child is None:
                raise FileNotFound(f"File not found: {path}")
            
            if child.is_dir():
                raise IsADirectory(f"Is a directory: {path}")
            
            # Free allocated pages
            blocks_used = (child.size + self.block_size - 1) // self.block_size
            if blocks_used > 0:
                self.superblock.free_blocks(blocks_used)
            
            # Unlink from parent
            parent.remove_child(filename)
            
            return True
        except Exception as e:
            print(f"Error removing file: {e}")
            return False
    
    def rmdir(self, path: str) -> bool:
        """Remove an empty directory"""
        try:
            parent, dirname = self._resolve_path(path)
            if parent is None:
                raise FileNotFound(f"Parent directory not found: {path}")
            
            child = parent.get_child(dirname)
            if child is None:
                raise FileNotFound(f"Directory not found: {path}")
            
            if not child.is_dir():
                raise NotADirectory(f"Not a directory: {path}")
            
            if len(child.children) > 0:
                raise DirectoryNotEmpty("Directory not empty")
            
            parent.remove_child(dirname)
            
            return True
        except Exception as e:
            print(f"Error removing directory: {e}")
            return False
    
    def stat(self, path: str) -> Optional[Dict]:
        """Get file statistics"""
        try:
            inode = self._get_inode(path) if path != '/' else self.superblock.root_inode
            if inode is None:
                raise FileNotFound(f"Path not found: {path}")
            
            blocks_used = (inode.size + self.block_size - 1) // self.block_size
            
            return {
                'inode': inode.ino,
                'type': 'dir' if inode.is_dir() else 'file',
                'permissions': oct(inode.permissions),
                'size': inode.size,
                'blocks': blocks_used,
                'created': datetime.fromtimestamp(inode.created_time).isoformat(),
                'modified': datetime.fromtimestamp(inode.modified_time).isoformat(),
            }
        except Exception as e:
            print(f"Error stat: {e}")
            return None
    
    def get_usage(self) -> Dict:
        """Get filesystem usage statistics"""
        return {
            'block_size': self.block_size,
            'total_blocks': self.superblock.max_blocks,
            'used_blocks': self.superblock.total_blocks,
            'free_blocks': self.superblock.get_available_blocks(),
            'total_size_mb': self.superblock.max_blocks * self.block_size / (1024 * 1024),
            'used_size_mb': self.superblock.total_blocks * self.block_size / (1024 * 1024),
            'usage_percent': (self.superblock.total_blocks / self.superblock.max_blocks * 100) if self.superblock.max_blocks > 0 else 0,
        }
    
    # ------------------------------------------------------------------
    # Snapshot persistence
    #
    # The on-disk format is content-addressed: each unique page is hashed
    # (SHA-256, truncated to 16 hex characters) and stored once in a
    # top-level `blobs` map keyed by that hash, with the bytes encoded as
    # base64. Inodes only carry a {page_index -> hash} mapping. This both
    # deduplicates identical pages (e.g. zero-padded files, repeated log
    # lines) and replaces hex (1 byte -> 2 chars) with base64
    # (3 bytes -> 4 chars), which keeps the JSON close to the raw payload
    # size instead of 2-3x larger.
    # ------------------------------------------------------------------

    SNAPSHOT_VERSION = 2
    _HASH_LEN = 16  # 64 bits of SHA-256 -> ample for educational sizes

    @staticmethod
    def _page_hash(page_bytes: bytes) -> str:
        return hashlib.sha256(page_bytes).hexdigest()[:VirtualFS._HASH_LEN]

    def save_snapshot(self, filepath: str) -> bool:
        """Serialize filesystem to a content-addressed JSON snapshot."""
        try:
            blobs: Dict[str, str] = {}

            def page_ref(page_bytes: bytes) -> str:
                h = self._page_hash(page_bytes)
                if h not in blobs:
                    blobs[h] = base64.b64encode(page_bytes).decode('ascii')
                return h

            def inode_to_dict(inode: Inode) -> Dict:
                return {
                    'ino': inode.ino,
                    'type': inode.file_type.name,
                    'permissions': inode.permissions,
                    'size': inode.size,
                    'created': inode.created_time,
                    'modified': inode.modified_time,
                    'pages': {str(k): page_ref(v) for k, v in inode.pages.items()},
                    'children': {name: inode_to_dict(child) for name, child in inode.children.items()}
                }

            root_dict = inode_to_dict(self.superblock.root_inode)

            snapshot = {
                'version': self.SNAPSHOT_VERSION,
                'timestamp': time.time(),
                'superblock': {
                    'block_size': self.superblock.block_size,
                    'max_blocks': self.superblock.max_blocks,
                    'total_blocks': self.superblock.total_blocks,
                    'created': self.superblock.created_time,
                },
                'blobs': blobs,
                'root': root_dict,
            }

            with open(filepath, 'w') as f:
                json.dump(snapshot, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return False

    def load_snapshot(self, filepath: str) -> bool:
        """Restore filesystem from a content-addressed JSON snapshot.

        Both the current (version 2, base64 + hash dedup) and the legacy
        (version 1, inline hex page bytes) layouts are accepted so older
        snapshots remain loadable.
        """
        try:
            with open(filepath, 'r') as f:
                snapshot = json.load(f)

            self.superblock = SuperBlock(
                block_size=snapshot['superblock']['block_size'],
                max_blocks=snapshot['superblock']['max_blocks']
            )

            blobs_b64 = snapshot.get('blobs', {})
            blobs: Dict[str, bytes] = {h: base64.b64decode(b64) for h, b64 in blobs_b64.items()}

            def resolve_pages(entry: Dict) -> Dict[int, bytes]:
                # New layout: {page_idx: hash}
                if 'pages' in entry:
                    return {int(k): blobs[h] for k, h in entry['pages'].items()}
                # Legacy layout: {page_idx: hex_string}
                if 'data' in entry:
                    return {int(k): bytes.fromhex(v) for k, v in entry['data'].items()}
                return {}

            def dict_to_inode(data: Dict) -> Inode:
                inode = Inode(
                    ino=data['ino'],
                    file_type=FileType[data['type']],
                    permissions=data['permissions'],
                    size=data['size'],
                    created_time=data['created'],
                    modified_time=data['modified'],
                    pages=resolve_pages(data),
                )
                for name, child_data in data['children'].items():
                    inode.children[name] = dict_to_inode(child_data)
                return inode

            self.superblock.root_inode = dict_to_inode(snapshot['root'])
            self.superblock.mounted = True
            self.superblock.total_blocks = snapshot['superblock']['total_blocks']

            return True
        except Exception as e:
            print(f"Error loading snapshot: {e}")
            return False
