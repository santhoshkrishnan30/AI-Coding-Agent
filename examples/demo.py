#!/usr/bin/env python3
"""
Demo script for AI Coding Agent
This script demonstrates the key features of the AI Coding Agent by running a series of commands.
"""

import subprocess
import time
import sys
import os

def run_agent_command(agent_process, command, timeout=30):
    """Send a command to the agent process and wait for the response."""
    print(f"\n> {command}")
    # Send the command
    agent_process.stdin.write(command + "\n")
    agent_process.stdin.flush()
    
    # Read output until we see the prompt again or timeout
    output = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = agent_process.stdout.readline()
        if not line:
            break
        output.append(line)
        print(line, end='')
        # Check for the prompt (this might need adjustment based on your actual prompt)
        if ">>> " in line or "Enter your command:" in line:
            break
    return ''.join(output)

def main():
    # Change to the project directory (assuming the script is run from the project root)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("=== AI Coding Agent Demo ===\n")
    
    # Start the agent
    print("Starting AI Coding Agent...")
    agent_process = subprocess.Popen(
        [sys.executable, "src/main_enhanced.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    # Wait for the agent to start (read initial output until prompt)
    print("Agent starting up...")
    initial_output = []
    while True:
        line = agent_process.stdout.readline()
        if not line:
            break
        initial_output.append(line)
        print(line, end='')
        if ">>> " in line or "Enter your command:" in line:
            break
    
    # Demo commands
    commands = [
        "help",
        "status",
        "list files in current directory",
        "read package.json",
        "write file hello.txt with content 'Hello, World!'",
        "read hello.txt",
        "git status",
        "set preference verbose_output true",
        "show preferences",
        "backup hello.txt and then add comment to it",
        "show learning",
        "exit"
    ]
    
    # Execute each command
    for cmd in commands:
        run_agent_command(agent_process, cmd)
        # Wait a bit between commands to avoid rate limiting
        time.sleep(2)
    
    # Wait for the agent to finish
    agent_process.wait()
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()