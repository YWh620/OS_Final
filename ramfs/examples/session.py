"""
Example 4: Session Storage

Manage user sessions in memory.
"""

import json
import time
from ramfs import VirtualFS


class SessionManager:
    """Session storage using RamFS"""
    
    def __init__(self, fs, session_dir="/sessions"):
        self.fs = fs
        self.session_dir = session_dir
        self.fs.mkdir(session_dir)
    
    def create(self, session_id, user_data):
        """Create new session"""
        session_file = f"{self.session_dir}/{session_id}.json"
        self.fs.touch(session_file)
        
        session = {
            "session_id": session_id,
            "created_at": time.time(),
            "user_data": user_data,
            "last_activity": time.time()
        }
        
        self.fs.write(session_file, json.dumps(session, indent=2))
    
    def get(self, session_id):
        """Get session data"""
        session_file = f"{self.session_dir}/{session_id}.json"
        data = self.fs.read(session_file)
        return json.loads(data) if data else None
    
    def destroy(self, session_id):
        """Destroy session"""
        session_file = f"{self.session_dir}/{session_id}.json"
        return self.fs.rm(session_file)
    
    def list_sessions(self):
        """List all active sessions"""
        entries = self.fs.ls(self.session_dir)
        sessions = []
        for entry in entries or []:
            session_id = entry['name'].replace('.json', '')
            session = self.get(session_id)
            sessions.append(session)
        return sessions


def demo():
    """Demonstrate session management"""
    
    fs = VirtualFS(max_size_mb=100)
    fs.mount()
    
    mgr = SessionManager(fs)
    
    print("Session Management Demo:")
    print("-" * 40)
    
    # Create sessions
    mgr.create("sess_001", {
        "user_id": 101,
        "username": "alice",
        "ip": "192.168.1.1"
    })
    print("✓ Created session sess_001")
    
    mgr.create("sess_002", {
        "user_id": 102,
        "username": "bob",
        "ip": "192.168.1.2"
    })
    print("✓ Created session sess_002")
    
    # List sessions
    print("\nActive Sessions:")
    for session in mgr.list_sessions():
        print(f"  {session['session_id']}: {session['user_data']['username']}")
    
    # Destroy session
    mgr.destroy("sess_001")
    print("\n✓ Destroyed sess_001")
    
    print("\nRemaining Sessions:")
    for session in mgr.list_sessions():
        print(f"  {session['session_id']}: {session['user_data']['username']}")
    
    fs.umount()


if __name__ == "__main__":
    demo()
