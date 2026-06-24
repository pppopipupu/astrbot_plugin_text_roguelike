import unittest
import os
import sys


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    discovered = loader.discover(os.path.join(start_dir, "rogue_tests"), pattern="test_*.py")
    suite.addTests(discovered)
    return suite

if __name__ == "__main__":
    unittest.main()
