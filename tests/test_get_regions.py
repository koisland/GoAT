import unittest

# from GoAT.logic.board import Board
from GoAT.vision.loader import load_board


class TestRegion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grid_v_5_5 = load_board("docs/images/5_5.png")
        cls.grid_v_9_9 = load_board("docs/images/9_9.png")

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_score(self):
        pass
