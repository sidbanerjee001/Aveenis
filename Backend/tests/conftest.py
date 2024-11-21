# tests/conftest.py allows files from parent direct to be found
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
