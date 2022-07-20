import unittest
import bidict
from collections import Counter

from GoAT.logic.board import Board
from GoAT.logic.scoring import Score
from GoAT.vision.loader import load_board


class TestScore(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grid_v_5_5 = load_board("docs/images/5_5.png")
        cls.grid_v_9_9 = load_board("docs/images/9_9.png")

        cls.chinese_scoreboard = Score("Chinese", komi=False)
        cls.japanese_scoreboard = Score("Japanese", komi=False)

    def setUp(self) -> None:
        # Reset counter.
        self.chinese_scoreboard.scores = Counter()
        self.japanese_scoreboard.scores = Counter()

    def test_score_chinese_5_5(self):
        board_v_5_5 = Board(
            grid=self.grid_v_5_5.copy(),
            captures=Counter({"Black": 0, "White": 0}),
            colors=bidict.bidict({"Black": 1.0, "White": 0.0}),
        ).clear_dead_regions()

        # Score board and declare score.
        expected_score = Counter({"Black": 13, "White": 12})
        score = self.chinese_scoreboard.score(board_v_5_5)
        self.assertEqual(expected_score, score)

    def test_score_chinese_9_9(self):
        board_v_9_9 = Board(
            grid=self.grid_v_9_9.copy(),
            captures=Counter({"Black": 0, "White": 0}),
            colors=bidict.bidict({"Black": 1.0, "White": 0.0}),
        ).clear_dead_regions()

        # Score board and declare score.
        expected_score = Counter({"Black": 44, "White": 37})
        score = self.chinese_scoreboard.score(board_v_9_9)
        self.assertEqual(expected_score, score)

    def test_score_japanese_5_5(self):
        captured_pieces = Counter({"Black": 1, "White": 2})
        board_v_5_5 = Board(
            grid=self.grid_v_5_5.copy(),
            captures=captured_pieces,
            colors=bidict.bidict({"Black": 1.0, "White": 0.0}),
        ).clear_dead_regions()

        # Score board and declare score.
        expected_score = Counter({"Black": 1, "White": 1})
        score = self.japanese_scoreboard.score(board_v_5_5)
        self.assertEqual(expected_score, score)

    def test_score_japanese_9_9(self):
        captured_pieces = Counter({"Black": 1, "White": 2})
        board_v_9_9 = Board(
            grid=self.grid_v_9_9.copy(),
            captures=captured_pieces,
            colors=bidict.bidict({"Black": 1.0, "White": 0.0}),
        ).clear_dead_regions()

        # Score board and declare score.
        expected_score = Counter({"Black": 15, "White": 9})
        score = self.japanese_scoreboard.score(board_v_9_9)
        self.assertEqual(expected_score, score)
