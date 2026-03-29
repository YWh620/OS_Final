"""
Example 3: In-Memory Logging System

Log events to RamFS with timestamps and levels.
"""

import time
from ramfs import VirtualFS


class RamFSLogger:
    """Simple logging system using RamFS"""
    
    def __init__(self, fs, log_dir="/logs"):
        self.fs = fs
        self.log_dir = log_dir
        self.fs.mkdir(log_dir)
    
    def log(self, name, level, message):
        """Write log entry"""
        log_file = f"{self.log_dir}/{name}.log"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {level:8s}: {message}\n"
        
        if not self.fs._get_inode(log_file):
            self.fs.touch(log_file)
        
        self.fs.append(log_file, entry)
    
    def read(self, name):
        """Read all logs for application"""
        log_file = f"{self.log_dir}/{name}.log"
        return self.fs.read(log_file)
    
    def size(self, name):
        """Get log file size"""
        log_file = f"{self.log_dir}/{name}.log"
        stat = self.fs.stat(log_file)
        return stat['size'] if stat else 0


def demo():
    """Demonstrate logging system"""
    
    fs = VirtualFS(max_size_mb=100)
    fs.mount()
    
    logger = RamFSLogger(fs)
    
    print("Logging Demo:")
    print("-" * 40)
    
    # Write logs
    logger.log("app1", "INFO", "Application started")
    logger.log("app1", "DEBUG", "Loading configuration")
    logger.log("app1", "INFO", "Ready to accept connections")
    
    logger.log("app2", "WARNING", "High memory usage detected")
    logger.log("app2", "ERROR", "Failed to connect to database")
    
    print("✓ Logs written")
    
    # Read logs
    print("\napp1.log:")
    print(logger.read("app1"))
    
    print("\napp2.log:")
    print(logger.read("app2"))
    
    # Stats
    print(f"app1 size: {logger.size('app1')} bytes")
    print(f"app2 size: {logger.size('app2')} bytes")
    
    fs.umount()


if __name__ == "__main__":
    demo()
