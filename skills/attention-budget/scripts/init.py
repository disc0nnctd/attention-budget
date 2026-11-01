#!/usr/bin/env python3
"""attention-budget: init. Stdlib only. Run from anywhere."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention_budget.cli import main
sys.exit(main(["init", *sys.argv[1:]]))
