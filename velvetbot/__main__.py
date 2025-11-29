"""VelvetBot Entry Point
Properly loads .env before importing any modules.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of velvetbot package)
# When running 'python -m velvetbot', __file__ will be velvetbot/__main__.py
package_dir = Path(__file__).parent  # velvetbot/
project_root = package_dir.parent     # velvetbot (project root)

# Load .env from project root
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Verify DISCORD_TOKEN is loaded
if not os.getenv('DISCORD_TOKEN'):
    print(f"ERROR: DISCORD_TOKEN not found!")
    print(f"Looking for .env at: {env_path}")
    print(f"File exists: {env_path.exists()}")
    if env_path.exists():
        print(f"\nContents of .env file:")
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Don't print the actual token value
                if line.strip() and not line.startswith('#'):
                    key = line.split('=')[0]
                    print(f"  Line {line_num}: {key}=***")
                elif line.strip():
                    print(f"  Line {line_num}: {line.strip()}")
    sys.exit(1)

# Now we can safely import bot
from .bot import main

if __name__ == '__main__':
    main()
