#!/usr/bin/env python3
"""
Simple log viewer for the EMR application
Usage: python view_logs.py [log_type]
log_type can be: app, error, gcp, all (default: all)
"""

import sys
import os
from datetime import datetime

def tail_log(filename, lines=50):
    """Read last N lines from log file"""
    if not os.path.exists(filename):
        return f"Log file {filename} does not exist"
    
    try:
        with open(filename, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception as e:
        return f"Error reading {filename}: {e}"

def view_logs(log_type='all', lines=50):
    """View logs based on type"""
    
    log_dir = 'logs'
    log_files = {
        'app': os.path.join(log_dir, 'app.log'),
        'error': os.path.join(log_dir, 'error.log'),
        'gcp': os.path.join(log_dir, 'gcp_api.log')
    }
    
    print("=" * 80)
    print(f"📋 EMR APPLICATION LOGS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if log_type == 'all':
        for log_name, log_file in log_files.items():
            print(f"\n📁 {log_name.upper()} LOG ({log_file}):")
            print("-" * 60)
            content = tail_log(log_file, lines)
            print(content)
            print("-" * 60)
    elif log_type in log_files:
        log_file = log_files[log_type]
        print(f"\n📁 {log_type.upper()} LOG ({log_file}):")
        print("-" * 60)
        content = tail_log(log_file, lines)
        print(content)
        print("-" * 60)
    else:
        print(f"❌ Unknown log type: {log_type}")
        print("Available types: app, error, gcp, all")
        return
    
    print("\n💡 Tips:")
    print("- Use 'python view_logs.py error' to see only error logs")
    print("- Use 'python view_logs.py app' to see application logs")
    print("- Use 'python view_logs.py gcp' to see Google Cloud API logs")
    print("- Logs rotate automatically when they reach 10MB")

if __name__ == "__main__":
    log_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    view_logs(log_type, lines)