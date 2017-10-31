import unittest
from microkanren.urkanren import *

class Test_CoreMicroKanren(unittest.TestCase):
    def test_base_var(self):
        self.assertEqual(var(1), [1])


if __name__ == "__main__":
    unittest.main()
