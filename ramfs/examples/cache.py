"""
Example 2: In-Memory Caching System

Using RamFS as a high-performance cache layer.
"""

import json
from ramfs import VirtualFS


class RamFSCache:
    """Simple caching system using RamFS"""
    
    def __init__(self, fs, cache_dir="/cache"):
        self.fs = fs
        self.cache_dir = cache_dir
        self.fs.mkdir(cache_dir)
    
    def get(self, key):
        """Get cached value"""
        path = f"{self.cache_dir}/{key}"
        return self.fs.read(path)
    
    def set(self, key, value):
        """Set cached value"""
        path = f"{self.cache_dir}/{key}"
        if not self.fs._get_inode(path):
            self.fs.touch(path)
        self.fs.write(path, value)
    
    def delete(self, key):
        """Delete from cache"""
        path = f"{self.cache_dir}/{key}"
        return self.fs.rm(path)
    
    def stats(self):
        """Get cache statistics"""
        entries = self.fs.ls(self.cache_dir)
        return {
            "items": len(entries) if entries else 0,
            "total_size": sum(e['size'] for e in entries) if entries else 0
        }


def demo():
    """Demonstrate caching system"""
    
    fs = VirtualFS(max_size_mb=100)
    fs.mount()
    
    cache = RamFSCache(fs)
    
    print("Caching Demo:")
    print("-" * 40)
    
    # Cache API response
    cache.set("user_123", json.dumps({
        "id": 123,
        "name": "Alice",
        "email": "alice@example.com"
    }))
    print("✓ Cached user_123")
    
    # Cache query result
    cache.set("query_result", json.dumps([
        {"id": 1, "title": "First"},
        {"id": 2, "title": "Second"}
    ]))
    print("✓ Cached query_result")
    
    # Get from cache
    user_data = cache.get("user_123")
    print(f"\nCache HIT: {json.loads(user_data)['name']}")
    
    # Stats
    stats = cache.stats()
    print(f"\nCache Stats:")
    print(f"  Items: {stats['items']}")
    print(f"  Size: {stats['total_size']} bytes")
    
    fs.umount()


if __name__ == "__main__":
    demo()
