"""
LibreGol TV — Background Automated Sync Daemon
Runs competitor_sync.py every 30 minutes (1800 seconds).
"""
import time
import datetime
import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYNC_SCRIPT = os.path.join(BASE_DIR, "auto_sync_pipeline.py")
INTERVAL_SECONDS = 1800  # 30 minutes

print("=== LibreGol TV Resilient Auto-Sync Daemon Started ===")
print("Tracking live matches via Primary Mirror & ESPN Fallback every 30 minutes...")
sys.stdout.flush()

while True:
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Triggering 30-minute sync cycle...")
        sys.stdout.flush()
        res = subprocess.run([sys.executable, SYNC_SCRIPT], capture_output=True, text=True, encoding="utf-8")
        if res.stdout:
            print(res.stdout.strip())
        if res.stderr:
            print("Errors:", res.stderr.strip())
        sys.stdout.flush()
    except Exception as e:
        print(f"Daemon cycle error: {e}")
        sys.stdout.flush()
    
    print(f"Next sync scheduled in 30 minutes ({INTERVAL_SECONDS}s). Sleeping...")
    sys.stdout.flush()
    time.sleep(INTERVAL_SECONDS)
