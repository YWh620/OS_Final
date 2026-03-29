"""
RamFS Interactive CLI

Command-line interface for the in-memory filesystem.
"""

import sys
import readline  # Enable command history and line editing (↑↓←→)
from ramfs import VirtualFS


class RamFSCLI:
    """Interactive CLI for RamFS"""
    
    def __init__(self, size_mb: int = 100):
        self.fs = VirtualFS(max_size_mb=size_mb)
        self.current_path = '/'
        self.running = False
    
    def mount(self):
        """Mount filesystem"""
        if not self.fs.mount():
            print("ERROR: Failed to mount filesystem")
            return False
        print(f"RamFS mounted (size: {self.fs.superblock.max_blocks * self.fs.block_size // (1024*1024)}MB)")
        return True
    
    def umount(self):
        """Unmount filesystem"""
        if self.fs.umount():
            print("Filesystem unmounted")
            return True
        return False
    
    def do_touch(self, args):
        """touch FILE - Create file"""
        if not args:
            print("Usage: touch FILE")
            return
        path = f"/{args[0]}" if not args[0].startswith('/') else args[0]
        if self.fs.touch(path):
            print(f"✓ Created {path}")
        else:
            print(f"✗ Failed to create {path}")
    
    def do_mkdir(self, args):
        """mkdir DIR - Create directory"""
        if not args:
            print("Usage: mkdir DIR")
            return
        path = f"/{args[0]}" if not args[0].startswith('/') else args[0]
        if self.fs.mkdir(path):
            print(f"✓ Created {path}")
        else:
            print(f"✗ Failed to create {path}")
    
    def do_cat(self, args):
        """cat FILE - Read file"""
        if not args:
            print("Usage: cat FILE")
            return
        path = f"/{args[0]}" if not args[0].startswith('/') else args[0]
        content = self.fs.read(path)
        if content is not None:
            print(content)
        else:
            print(f"✗ Cannot read {path}")
    
    def do_echo(self, args):
        """echo TEXT > FILE - Write to file"""
        if '>' not in args:
            print("Usage: echo TEXT > FILE")
            return
        idx = args.index('>')
        text = ' '.join(args[:idx])
        filepath = args[idx + 1] if idx + 1 < len(args) else None
        if not filepath:
            print("Usage: echo TEXT > FILE")
            return
        path = f"/{filepath}" if not filepath.startswith('/') else filepath
        if self.fs.write(path, text):
            print(f"✓ Wrote to {path}")
        else:
            print(f"✗ Failed to write to {path}")
    
    def do_ls(self, args):
        """ls [DIR] - List directory"""
        path = f"/{args[0]}" if args and not args[0].startswith('/') else (args[0] if args else '/')
        entries = self.fs.ls(path)
        if entries is None:
            print(f"✗ Cannot list {path}")
            return
        if not entries:
            print(f"{path} is empty")
            return
        for entry in entries:
            ftype = "d" if entry['type'] == 'dir' else "-"
            print(f"{ftype} {entry['name']:30} {entry['size']:10}")
    
    def do_rm(self, args):
        """rm FILE - Remove file"""
        if not args:
            print("Usage: rm FILE")
            return
        path = f"/{args[0]}" if not args[0].startswith('/') else args[0]
        if self.fs.rm(path):
            print(f"✓ Removed {path}")
        else:
            print(f"✗ Failed to remove {path}")
    
    def do_rmdir(self, args):
        """rmdir DIR - Remove directory"""
        if not args:
            print("Usage: rmdir DIR")
            return
        path = f"/{args[0]}" if not args[0].startswith('/') else args[0]
        if self.fs.rmdir(path):
            print(f"✓ Removed {path}")
        else:
            print(f"✗ Failed to remove {path}")
    
    def do_stat(self, args):
        """stat FILE - Show file info"""
        if not args:
            print("Usage: stat FILE")
            return
        path = f"/{args[0]}" if not args[0].startswith('/') else args[0]
        info = self.fs.stat(path)
        if info is None:
            print(f"✗ Cannot stat {path}")
            return
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    def do_df(self, args):
        """df - Show filesystem usage"""
        usage = self.fs.get_usage()
        print(f"\nTotal: {usage['total_size_mb']:.2f}MB")
        print(f"Used:  {usage['used_size_mb']:.2f}MB")
        print(f"Free:  {usage['total_size_mb'] - usage['used_size_mb']:.2f}MB")
        print(f"Use%:  {usage['usage_percent']:.1f}%")
    
    def do_save(self, args):
        """save FILE - Save snapshot"""
        if not args:
            print("Usage: save FILE")
            return
        if self.fs.save_snapshot(args[0]):
            print(f"✓ Saved to {args[0]}")
        else:
            print(f"✗ Failed to save")
    
    def do_load(self, args):
        """load FILE - Load snapshot"""
        if not args:
            print("Usage: load FILE")
            return
        if self.fs.load_snapshot(args[0]):
            print(f"✓ Loaded from {args[0]}")
        else:
            print(f"✗ Failed to load")
    
    def do_help(self, args):
        """help - Show commands"""
        commands = [
            "mount         - Mount filesystem",
            "umount        - Unmount filesystem",
            "touch FILE    - Create file",
            "mkdir DIR     - Create directory",
            "cat FILE      - Read file",
            "echo TEXT > F - Write to file",
            "ls [DIR]      - List directory",
            "rm FILE       - Remove file",
            "rmdir DIR     - Remove directory",
            "stat FILE     - Show file info",
            "df            - Disk usage",
            "save FILE     - Save snapshot",
            "load FILE     - Load snapshot",
            "help          - Show this help",
            "exit          - Exit",
        ]
        print("\nAvailable Commands:")
        for cmd in commands:
            print(f"  {cmd}")
        print()
    
    def run(self):
        """Start interactive shell"""
        self.running = True
        print("\nRamFS CLI - In-Memory File System Shell")
        print("Type 'help' for available commands\n")
        
        if not self.mount():
            return
        
        while self.running:
            try:
                prompt = f"ramfs:{self.current_path}> "
                line = input(prompt).strip()
                
                if not line:
                    continue
                
                parts = line.split()
                cmd = parts[0]
                args = parts[1:]
                
                if cmd == 'exit' or cmd == 'quit':
                    self.running = False
                    self.umount()
                    print("Goodbye!")
                    break
                elif cmd == 'mount':
                    self.mount()
                elif cmd == 'umount':
                    self.umount()
                elif cmd == 'touch':
                    self.do_touch(args)
                elif cmd == 'mkdir':
                    self.do_mkdir(args)
                elif cmd == 'cat':
                    self.do_cat(args)
                elif cmd == 'echo':
                    self.do_echo(args)
                elif cmd == 'ls':
                    self.do_ls(args)
                elif cmd == 'rm':
                    self.do_rm(args)
                elif cmd == 'rmdir':
                    self.do_rmdir(args)
                elif cmd == 'stat':
                    self.do_stat(args)
                elif cmd == 'df':
                    self.do_df(args)
                elif cmd == 'save':
                    self.do_save(args)
                elif cmd == 'load':
                    self.do_load(args)
                elif cmd == 'help' or cmd == '?':
                    self.do_help(args)
                else:
                    print(f"Unknown command: {cmd}")
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except EOFError:
                self.running = False
                self.umount()
                print("Goodbye!")
                break
            except Exception as e:
                print(f"ERROR: {e}")


def main():
    """CLI entry point"""
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        size_mb = int(sys.argv[1])
        cli = RamFSCLI(size_mb)
    else:
        cli = RamFSCLI(100)
    
    cli.run()


if __name__ == "__main__":
    main()
