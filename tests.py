"""
RamFS Test Suite

Complete tests for core functionality.
"""

from ramfs import VirtualFS, FileType


def test_basic_operations():
    """TEST 1: Basic operations"""
    print("\n" + "="*60)
    print("TEST 1: Basic Operations (touch, mkdir, write, read)")
    print("="*60)
    
    fs = VirtualFS(max_size_mb=10)
    assert fs.mount(), "Mount failed"
    print("✓ Filesystem mounted")
    
    assert fs.mkdir("/dir1"), "Failed to create /dir1"
    print("✓ Created /dir1")
    
    assert fs.touch("/file1.txt"), "Failed to create /file1.txt"
    print("✓ Created /file1.txt")
    
    assert fs.write("/file1.txt", "Hello RamFS!"), "Write failed"
    print("✓ Wrote to /file1.txt")
    
    content = fs.read("/file1.txt")
    assert content == "Hello RamFS!", f"Read mismatch: {content}"
    print(f"✓ Read from /file1.txt: '{content}'")
    
    assert fs.append("/file1.txt", "\nLine 2"), "Append failed"
    print("✓ Appended data")
    
    print("\n✓ TEST 1 PASSED\n")


def test_directory_listing():
    """TEST 2: Directory listing"""
    print("="*60)
    print("TEST 2: Directory Listing (ls, stat)")
    print("="*60)
    
    fs = VirtualFS(max_size_mb=10)
    fs.mount()
    
    fs.mkdir("/home")
    fs.mkdir("/home/user")
    fs.touch("/home/user/file1.txt")
    fs.touch("/home/user/file2.txt")
    
    entries = fs.ls("/home/user")
    assert len(entries) == 2, f"Expected 2 files, got {len(entries)}"
    print(f"✓ Listed 2 files in /home/user")
    
    stat_info = fs.stat("/home/user/file1.txt")
    assert stat_info is not None, "stat failed"
    print(f"✓ Got file info: inode={stat_info['inode']}")
    
    print("\n✓ TEST 2 PASSED\n")


def test_file_operations():
    """TEST 3: File operations"""
    print("="*60)
    print("TEST 3: File Operations (overwrite, delete)")
    print("="*60)
    
    fs = VirtualFS(max_size_mb=10)
    fs.mount()
    
    fs.touch("/test.txt")
    fs.write("/test.txt", "Version 1")
    print("✓ Wrote version 1")
    
    fs.write("/test.txt", "Version 2")
    content = fs.read("/test.txt")
    assert content == "Version 2", "Overwrite failed"
    print("✓ Overwrote file")
    
    assert fs.rm("/test.txt"), "Failed to remove file"
    assert fs.read("/test.txt") is None, "File should be deleted"
    print("✓ Removed file")
    
    print("\n✓ TEST 3 PASSED\n")


def test_memory_quota():
    """TEST 4: Memory quota"""
    print("="*60)
    print("TEST 4: Memory Quota (ENOSPC)")
    print("="*60)
    
    fs = VirtualFS(max_size_mb=1)  # 1MB limit
    fs.mount()
    
    fs.touch("/file1.txt")
    large_data = "X" * (512 * 1024)  # 512KB
    
    assert fs.write("/file1.txt", large_data), "Failed to write 512KB"
    print("✓ Wrote 512KB")
    
    usage = fs.get_usage()
    print(f"✓ Usage: {usage['used_size_mb']:.2f}MB / {usage['total_size_mb']:.2f}MB")
    
    fs.touch("/file2.txt")
    data2 = "Y" * (600 * 1024)  # 600KB - should fail
    
    result = fs.write("/file2.txt", data2)
    assert not result, "Should reject write exceeding quota"
    print("✓ Quota enforcement working (ENOSPC)")
    
    print("\n✓ TEST 4 PASSED\n")


def test_persistence():
    """TEST 5: Persistence"""
    print("="*60)
    print("TEST 5: Persistence (Save/Load Snapshots)")
    print("="*60)
    
    import os
    
    fs1 = VirtualFS(max_size_mb=10)
    fs1.mount()
    
    fs1.mkdir("/documents")
    fs1.touch("/documents/readme.txt")
    fs1.write("/documents/readme.txt", "Test content")
    print("✓ Created files")
    
    snapshot_file = "test_snapshot.json"
    assert fs1.save_snapshot(snapshot_file), "Failed to save"
    print(f"✓ Saved snapshot")
    
    fs2 = VirtualFS()
    assert fs2.load_snapshot(snapshot_file), "Failed to load"
    print("✓ Loaded snapshot")
    
    content = fs2.read("/documents/readme.txt")
    assert content == "Test content", "Content mismatch"
    print("✓ Verified data integrity")
    
    if os.path.exists(snapshot_file):
        os.remove(snapshot_file)
    
    print("\n✓ TEST 5 PASSED\n")


def test_error_handling():
    """TEST 6: Error handling"""
    print("="*60)
    print("TEST 6: Error Handling")
    print("="*60)
    
    fs = VirtualFS(max_size_mb=10)
    fs.mount()
    
    # Missing file
    content = fs.read("/nonexistent.txt")
    assert content is None, "Should return None for missing file"
    print("✓ Handled missing file")
    
    # Missing parent
    result = fs.touch("/nonexistent/file.txt")
    assert not result, "Should fail for missing parent"
    print("✓ Handled missing parent directory")
    
    # File/directory type mismatch
    fs.mkdir("/mydir")
    content = fs.read("/mydir")
    assert content is None, "Should not read from directory"
    print("✓ Prevented reading directory as file")
    
    # Non-empty directory
    fs.touch("/fulldir")  # Create as file first
    fs.rmdir("/fulldir")  # This should fail but won't fail at rmdir
    fs.mkdir("/fulldir")
    fs.touch("/fulldir/inner.txt")
    result = fs.rmdir("/fulldir")
    assert not result, "Should not remove non-empty directory"
    print("✓ Prevented removing non-empty directory")
    
    print("\n✓ TEST 6 PASSED\n")


def test_stress():
    """TEST 7: Stress test"""
    print("="*60)
    print("TEST 7: Stress Test (Many Files)")
    print("="*60)
    
    fs = VirtualFS(max_size_mb=20)
    fs.mount()
    
    # Create many files
    for i in range(3):
        fs.mkdir(f"/dir{i}")
        for j in range(10):
            fs.touch(f"/dir{i}/file{j}.txt")
            fs.write(f"/dir{i}/file{j}.txt", f"Content {i}-{j}\n" * 5)
    
    print("✓ Created 30 files")
    
    usage = fs.get_usage()
    print(f"✓ Usage: {usage['used_size_mb']:.2f}MB")
    
    print("\n✓ TEST 7 PASSED\n")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║            RAMFS TEST SUITE - All Tests                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        test_basic_operations()
        test_directory_listing()
        test_file_operations()
        test_memory_quota()
        test_persistence()
        test_error_handling()
        test_stress()
        
        print("="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
