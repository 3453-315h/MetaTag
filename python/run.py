#!/usr/bin/env python3
"""Run MetaTag directly."""

import sys
import os

# Add the current directory to sys.path so that 'metatag' package can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metatag.ui.main_window import main

if __name__ == "__main__":
    sys.exit(main())
