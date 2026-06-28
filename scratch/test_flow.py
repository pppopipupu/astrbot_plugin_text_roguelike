import unittest
import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_curr_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)



def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    discovered = loader.discover(os.path.join(start_dir, "rogue_tests"), pattern="test_*.py")
    suite.addTests(discovered)
    return suite

if __name__ == "__main__":
    unittest.main()
