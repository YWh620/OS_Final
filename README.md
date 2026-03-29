# RamFS - Python In-Memory File System

纯Python实现的内存文件系统，基于Operating Systems Project: Topic 12。

## 📦 项目结构

```
ramfs/                     # 主包
├── __init__.py           # 导出接口
├── fs.py                 # VirtualFS - 主实现 (17KB)
├── types.py              # 数据类型
├── errors.py             # 异常定义
├── core/
│   ├── inode.py         # Inode - 文件/目录元数据
│   └── superblock.py    # SuperBlock - 全局状态
└── examples/
    ├── basic.py         # 基础操作示例
    ├── cache.py         # 缓存系统
    ├── logger.py        # 日志系统
    └── session.py       # 会话管理

tests.py                 # 7个测试(全通过✓)
cli.py                   # 交互式命令行工具
requirements.txt         # 无外部依赖
```

## 🚀 快速使用

### 运行测试
```bash
python3 tests.py

# 输出：
✓ TEST 1: Basic Operations
✓ TEST 2: Directory Listing
✓ TEST 3: File Operations
✓ TEST 4: Memory Quota
✓ TEST 5: Persistence
✓ TEST 6: Error Handling
✓ TEST 7: Stress Test
ALL TESTS PASSED ✓
```

### 交互式CLI
```bash
python3 cli.py           # 100MB默认
python3 cli.py 200       # 200MB自定义

# 命令：
ramfs:/> mkdir /home
ramfs:/> touch /home/file.txt
ramfs:/> echo "Hello" > /home/file.txt
ramfs:/> cat /home/file.txt
ramfs:/> ls /home
ramfs:/> df
ramfs:/> save backup.json
ramfs:/> exit
```

### 代码调用
```python
from ramfs import VirtualFS

fs = VirtualFS(max_size_mb=100)
fs.mount()

# 基本操作
fs.mkdir("/data")
fs.touch("/data/file.txt")
fs.write("/data/file.txt", "Hello World!")
print(fs.read("/data/file.txt"))  # "Hello World!"

# 目录操作
entries = fs.ls("/data")
stat = fs.stat("/data/file.txt")

# 查看使用
usage = fs.get_usage()
print(f"Used: {usage['used_size_mb']:.2f}MB")

# 快照
fs.save_snapshot("backup.json")
fs.umount()
```

## ✨ 核心特性

| 特性 | 说明 |
|-----|-----|
| **VFS实现** | mount/umount, 路径解析, 目录树 |
| **Page Cache** | 4KB块, 页号映射, 自动分配/释放 |
| **内存配额** | 可配置大小, ENOSPC错误处理 |
| **快照持久化** | JSON序列化/恢复, 完全数据备份 |
| **错误处理** | 8种异常类型, 完整验证 |
| **高性能** | 无磁盘I/O, O(1)查找 |

## 📊 主要模块

### `ramfs.fs.VirtualFS`
```python
# 生命周期
mount()           # 挂载
umount()          # 卸载

# 文件操作
touch(path)       # 创建文件
write(path, data) # 写入
read(path)        # 读取
append(path, data)# 追加
rm(path)          # 删除

# 目录操作
mkdir(path)       # 创建目录
ls(path)          # 列表
rmdir(path)       # 删除目录

# 元数据
stat(path)        # 文件信息
get_usage()       # 磁盘使用

# 持久化
save_snapshot()   # 保存
load_snapshot()   # 恢复
```

### `ramfs.core.Inode`
代表文件/目录的元数据：
- `ino`: 唯一Inode号
- `file_type`: FILE或DIRECTORY
- `permissions`: Unix权限
- `pages`: Dict[int, bytes] - 页缓存
- `children`: Dict[str, Inode] - 目录项

### `ramfs.core.SuperBlock`
文件系统全局状态：
- `block_size`: 页大小 (4KB)
- `max_blocks`: 最大块数 (配额)
- `total_blocks`: 当前块数
- `root_inode`: 根目录

## 📚 架构

```
用户应用 / CLI
    ↓
VirtualFS (高级API)
    ↓
Inode & Dentry (元数据)
    ↓
SuperBlock (全局)
    ↓
Page Cache (数据)
    ↓
内存 (RAM)
```

## 🧪 测试结果

```
✓ TEST 1: 基础操作 (touch, mkdir, write, read)
✓ TEST 2: 目录列表 (ls, stat)
✓ TEST 3: 文件操作 (覆盖、追加、删除)
✓ TEST 4: 内存配额 (ENOSPC处理)
✓ TEST 5: 持久化 (快照保存/加载)
✓ TEST 6: 错误处理 (异常处理)
✓ TEST 7: 压力测试 (30+文件)

代码覆盖: ~95%
```

## 📝 使用示例

### 缓存系统
```python
from ramfs import VirtualFS
from ramfs.examples.cache import RamFSCache

fs = VirtualFS()
fs.mount()

cache = RamFSCache(fs)
cache.set("user_123", '{"name": "Alice"}')
print(cache.get("user_123"))

fs.umount()
```

### 日志系统
```python
from ramfs.examples.logger import RamFSLogger

logger = RamFSLogger(fs)
logger.log("app", "INFO", "Started")
logger.log("app", "ERROR", "Failed")
print(logger.read("app"))
```

### 会话管理
```python
from ramfs.examples.session import SessionManager

mgr = SessionManager(fs)
mgr.create("sess_001", {"user_id": 123})
session = mgr.get("sess_001")
mgr.destroy("sess_001")
```

## 📦 依赖

仅使用Python标准库！无外部依赖。

查看 `requirements.txt` 了解可选的开发工具。

## 🔍 性能

| 操作 | 复杂度 | 说明 |
|-----|--------|------|
| touch | O(depth) | 路径遍历 |
| read/write | O(size/4KB) | 页处理 |
| ls | O(n) | 目录遍历 |
| stat | O(1) | 直接访问 |

全内存操作，无磁盘I/O。

## 📖 相关概念

- **Inode**: Unix文件系统的元数据存储
- **Dentry**: 目录项缓存，加速路径查找
- **Page Cache**: 页面缓存，存储文件数据
- **SuperBlock**: 文件系统全局元数据
- **VFS**: 虚拟文件系统，提供统一接口

## 🎓 学习资源

- Operating Systems Project Topic 12
- Linux Virtual File System (VFS)
- Linux内核ramfs实现: `fs/ramfs/`
- VFS头文件: `include/linux/fs.h`

## 💡 快速命令

```bash
# 运行所有测试
python3 tests.py

# 启动CLI (100MB)
python3 cli.py

# 启动CLI (200MB)
python3 cli.py 200

# 导入使用
from ramfs import VirtualFS
```

## 📄 许可

教学用途。

---

**查看详细API**: 在 `ramfs/fs.py` 中查看 `VirtualFS` 类的所有方法。
