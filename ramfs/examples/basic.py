"""
Example 1: Basic Filesystem Operations

Demonstrates basic file and directory operations.
"""

from ramfs import VirtualFS


def create_project_structure():
    """Create a basic project directory structure"""
    
    fs = VirtualFS(max_size_mb=50)
    fs.mount()
    
    # Create project structure
    fs.mkdir("/project")
    fs.mkdir("/project/src")
    fs.mkdir("/project/docs")
    fs.mkdir("/project/config")
    
    # Create source files
    fs.touch("/project/src/main.py")
    fs.write("/project/src/main.py", """#!/usr/bin/env python3
def main():
    print("Hello from RamFS!")

if __name__ == "__main__":
    main()
""")
    
    # Create config
    fs.touch("/project/config/settings.json")
    fs.write("/project/config/settings.json", """{
  "app_name": "RamFS Demo",
  "version": "1.0",
  "debug": true
}""")
    
    # Create README
    fs.touch("/project/README.md")
    fs.write("/project/README.md", """# Project Documentation

A complete project stored in memory.

## Structure
- src/: Source code
- docs/: Documentation
- config/: Configuration
""")
    
    print("✓ Project structure created")
    print("\nDirectory contents:")
    entries = fs.ls("/project")
    for entry in entries:
        print(f"  {entry['name']:20} ({entry['type']:4})")
    
    usage = fs.get_usage()
    print(f"\nUsage: {usage['used_size_mb']:.2f}MB / {usage['total_size_mb']:.2f}MB")
    
    fs.umount()


if __name__ == "__main__":
    create_project_structure()
