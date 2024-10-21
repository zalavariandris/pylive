"""restart an application in safe mode if inactive for a while"""
import threading
import time
import os
import sys
import signal

class Watchdog(threading.Thread):
    def __init__(self, timeout: int):
        super().__init__()
        self.timeout = timeout
        self.last_heartbeat = time.time()
        self.daemon = True  # Set as a daemon so it ends with the program
        self.running = True

    def heartbeat(self):
        # Call this to notify the watchdog that the main thread is still running
        self.last_heartbeat = time.time()

    def run(self):
        # Keep checking whether the main thread is stuck
        while self.running:
            if time.time() - self.last_heartbeat > self.timeout:
                print("Watchdog: Main thread is stuck, restarting...")
                self.restart_program()
            time.sleep(1)

    def restart_program(self):
        """Restarts the current program by re-executing the script."""
        print("Restarting program...")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def stop(self):
        self.running = False

def main_thread_task(watchdog: Watchdog):
    # Simulate a task that could get stuck
    try:
        while True:
            print("Main thread running...")
            time.sleep(1)
            watchdog.heartbeat()  # Let the watchdog know the thread is alive
    except Exception as e:
        print(f"Error in main thread: {e}")

if __name__ == "__main__":
    watchdog = Watchdog(timeout=5)  # Set a timeout of 5 seconds
    watchdog.start()

    # Simulate running the main thread's task
    try:
        main_thread_task(watchdog)
    except KeyboardInterrupt:
        print("Stopping program...")
    finally:
        watchdog.stop()
