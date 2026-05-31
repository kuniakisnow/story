#!/usr/bin/env python3
"""
Publish the latest generated post to GitHub.
Usage: python scripts/publish.py [commit_message]
"""

import subprocess
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent


def git(*args):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Git error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "Update blog posts"

    # Check for changes
    status = git("status", "--porcelain")
    if not status:
        print("No changes to publish.")
        return

    # Stage, commit, push
    git("add", "-A")
    git("commit", "-m", msg)
    git("push", "origin", "main")

    print("Published successfully!")


if __name__ == "__main__":
    main()
