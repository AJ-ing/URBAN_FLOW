import os
import sys

# Add project root to path so we can import root modules
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Change CWD to project root so asset loading relative paths resolve correctly
os.chdir(ROOT_DIR)

import asyncio

import main

if __name__ == "__main__":
    asyncio.run(main.main())
