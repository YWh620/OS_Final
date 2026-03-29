"""
RamFS Exception Definitions
"""


class RamFSError(Exception):
    """Base exception for RamFS errors"""
    pass


class FileSystemNotMounted(RamFSError):
    """Raised when operation attempted on unmounted filesystem"""
    pass


class FileNotFound(RamFSError):
    """File or directory not found"""
    pass


class FileExists(RamFSError):
    """File already exists"""
    pass


class IsADirectory(RamFSError):
    """Operation attempted on directory instead of file"""
    pass


class NotADirectory(RamFSError):
    """Operation attempted on file instead of directory"""
    pass


class DirectoryNotEmpty(RamFSError):
    """Cannot delete non-empty directory"""
    pass


class NoSpaceLeft(RamFSError):
    """No space left on device (quota exceeded)"""
    pass


class InvalidPath(RamFSError):
    """Invalid path provided"""
    pass
