import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.core import Agent

def main():
    agent = Agent()
    agent.run()

if __name__ == "__main__":
    main()