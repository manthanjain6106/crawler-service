#!/usr/bin/env python3
"""
Worker management script for the crawler service.
Provides commands to start, stop, and monitor background workers.
"""

import argparse
import subprocess
import sys
import time
import signal
import os
from typing import List, Optional


class WorkerManager:
    def __init__(self):
        self.worker_processes: List[subprocess.Popen] = []
    
    def start_worker(self, count: int = 1, log_level: str = "INFO") -> None:
        """Start background workers."""
        print(f"Starting {count} worker(s) with log level {log_level}...")
        
        for i in range(count):
            env = os.environ.copy()
            env['LOG_LEVEL'] = log_level
            
            process = subprocess.Popen(
                [sys.executable, "background_jobs.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.worker_processes.append(process)
            print(f"Started worker {i+1} with PID {process.pid}")
        
        print(f"✅ Started {count} worker(s)")
    
    def stop_workers(self) -> None:
        """Stop all background workers."""
        if not self.worker_processes:
            print("No workers running")
            return
        
        print(f"Stopping {len(self.worker_processes)} worker(s)...")
        
        for i, process in enumerate(self.worker_processes):
            try:
                process.terminate()
                process.wait(timeout=10)
                print(f"Stopped worker {i+1} (PID {process.pid})")
            except subprocess.TimeoutExpired:
                print(f"Force killing worker {i+1} (PID {process.pid})")
                process.kill()
            except Exception as e:
                print(f"Error stopping worker {i+1}: {e}")
        
        self.worker_processes.clear()
        print("✅ All workers stopped")
    
    def status(self) -> None:
        """Show worker status."""
        if not self.worker_processes:
            print("No workers running")
            return
        
        print(f"Running {len(self.worker_processes)} worker(s):")
        for i, process in enumerate(self.worker_processes):
            status = "running" if process.poll() is None else "stopped"
            print(f"  Worker {i+1}: PID {process.pid} - {status}")
    
    def monitor(self, interval: int = 5) -> None:
        """Monitor workers and restart if they die."""
        print(f"Monitoring workers (checking every {interval}s)...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                # Check if any workers have died
                dead_workers = []
                for i, process in enumerate(self.worker_processes):
                    if process.poll() is not None:
                        dead_workers.append(i)
                        print(f"⚠️ Worker {i+1} (PID {process.pid}) has died")
                
                # Restart dead workers
                for i in reversed(dead_workers):
                    process = self.worker_processes.pop(i)
                    print(f"Restarting worker {i+1}...")
                    env = os.environ.copy()
                    new_process = subprocess.Popen(
                        [sys.executable, "background_jobs.py"],
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    self.worker_processes.insert(i, new_process)
                    print(f"Restarted worker {i+1} with PID {new_process.pid}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            self.stop_workers()
    
    def cleanup(self) -> None:
        """Clean up on exit."""
        self.stop_workers()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Manage crawler service workers")
    parser.add_argument("command", choices=["start", "stop", "status", "monitor"], 
                       help="Command to execute")
    parser.add_argument("--count", "-c", type=int, default=1, 
                       help="Number of workers to start")
    parser.add_argument("--log-level", "-l", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Log level for workers")
    parser.add_argument("--interval", "-i", type=int, default=5,
                       help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager = WorkerManager()
    
    try:
        if args.command == "start":
            manager.start_worker(args.count, args.log_level)
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
                manager.cleanup()
        
        elif args.command == "stop":
            manager.stop_workers()
        
        elif args.command == "status":
            manager.status()
        
        elif args.command == "monitor":
            manager.start_worker(args.count, args.log_level)
            manager.monitor(args.interval)
    
    except Exception as e:
        print(f"Error: {e}")
        manager.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
