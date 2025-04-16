#!/usr/bin/env python3
"""
Test script to demonstrate the streaming mode functionality of DupeRemover.
This script will:
1. Generate a test log file
2. Continuously append lines to it, including duplicates
3. Allow DupeRemover to process it in streaming mode
"""

import os
import sys
import time
import random
import threading
import argparse
from datetime import datetime


# Sample log lines to use in our test
LOG_LINES = [
    "[INFO] Application started successfully",
    "[INFO] Connection established to database",
    "[INFO] User login successful: user123",
    "[INFO] User login successful: admin",
    "[ERROR] Database connection timeout",
    "[WARNING] High CPU usage detected: 85%",
    "[WARNING] High memory usage detected: 78%",
    "[ERROR] Failed to process request: timeout",
    "[INFO] Cache cleared successfully",
    "[INFO] Background job completed successfully",
    "[DEBUG] Processing item #42 in queue",
    "[DEBUG] API response received: 200 OK",
    "[ERROR] Failed to send email notification",
    "[WARNING] Disk space low: 15% remaining",
    "[INFO] Configuration reloaded"
]


def generate_log_entries(log_file, duration=60, interval=0.5, duplicate_rate=0.3):
    """
    Generate simulated log entries with some duplicates.
    
    Args:
        log_file: Path to the log file to write
        duration: How long to run in seconds
        interval: How often to write entries (seconds)
        duplicate_rate: Probability of writing a duplicate
    """
    start_time = time.time()
    end_time = start_time + duration
    
    # Create or clear the log file
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"# Test log file created at {datetime.now().isoformat()}\n")
    
    print(f"Generating log entries to {log_file} for {duration} seconds...")
    print(f"Press Ctrl+C to stop early")
    
    try:
        while time.time() < end_time:
            # Decide whether to write a duplicate
            if random.random() < duplicate_rate and os.path.getsize(log_file) > 0:
                # Read a random line from the existing file
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:  # Ensure we have at least one line to duplicate
                        duplicate_line = random.choice(lines[1:])  # Skip the header line
                        
                        # Append the duplicate
                        with open(log_file, 'a', encoding='utf-8') as f:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                            f.write(f"{timestamp} {duplicate_line}")
            else:
                # Write a new random log entry
                with open(log_file, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    log_entry = random.choice(LOG_LINES)
                    f.write(f"{timestamp} {log_entry}\n")
            
            # Sleep for the specified interval
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nLog generation stopped by user")
    
    print(f"Finished generating logs to {log_file}")


def run_streaming_demo(log_file, duration):
    """
    Run a demonstration of the streaming mode functionality.
    
    Args:
        log_file: Path to the log file
        duration: How long to run in seconds
    """
    # Start the log generator in a separate thread
    generator_thread = threading.Thread(
        target=generate_log_entries,
        args=(log_file, duration, 0.2, 0.4),
        daemon=True
    )
    generator_thread.start()
    
    # Instruct the user to run the streaming mode
    print("\n" + "="*60)
    print(" STREAMING MODE DEMONSTRATION")
    print("="*60)
    print("\nA test log file is being generated with random entries and duplicates.")
    print("To see the streaming mode in action, run this command in another terminal:")
    print(f"\npython main.py {log_file} --stream --follow\n")
    print("Or to see all lines including duplicates:")
    print(f"\ntype {log_file}  # Windows\n")
    print(f"cat {log_file}   # Linux/Mac\n")
    print("="*60 + "\n")
    
    # Wait for the generator thread to finish
    generator_thread.join()
    
    # Show some stats about the generated file
    if os.path.exists(log_file):
        total_lines = sum(1 for _ in open(log_file, 'r', encoding='utf-8'))
        file_size = os.path.getsize(log_file)
        print(f"\nTest completed:")
        print(f"- Log file: {log_file}")
        print(f"- Size: {file_size/1024:.2f} KB")
        print(f"- Lines: {total_lines}")
        print("\nYou can now process this file with DupeRemover in various modes.")


def parse_args():
    parser = argparse.ArgumentParser(description="Test script for DupeRemover streaming mode")
    parser.add_argument(
        "--output", "-o",
        default="test_log.txt",
        help="Path to the output log file (default: test_log.txt)"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=60,
        help="Duration in seconds to generate logs (default: 60)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_streaming_demo(args.output, args.duration)


if __name__ == "__main__":
    main() 