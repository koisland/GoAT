from __future__ import annotations
import collections
import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Dict

logger = logging.getLogger("logic")
SCORING_SYSTEMS = ["Japanese", "Chinese"]
# https://senseis.xmp.net/?JapaneseCountingExample
# https://senseis.xmp.net/?ChineseCountingExample

@dataclass
class Score:

    system: str
    komi: bool = True
    scores: Dict[str, int] = field(init=False)

    def validate_fields(self):
        if self.system not in SCORING_SYSTEMS:
            raise Exception("Invalid scoring system.")

    def __post_init__(self):
        self.validate_fields()

    @property
    def default_komi(self) -> float:
        """
        Set default komi for scoring methods
        https://senseis.xmp.net/?Komi

        """
        komi = {
            "Chinese": 7.5,
            "Japanese": 6.5
        }
        return komi[self.system]

    def declare_winner(self) -> Dict[str, int]:
        """
        Display log message and return scores.
        Assumes komi has already been added.

        :return: scores for each group
        """
        if self.scores["Black"] == self.scores["White"]:
            logger.info(f"Tie game. {self.scores}")
        if self.scores["Black"] > self.scores["White"]:
            logger.info(f"Black wins. {self.scores}")
        else:
            logger.info(f"White wins. {self.scores}")
        
        return self.scores

    def _score_chinese(self, board) -> Score:
        # Count pieces and empty regions
        # For chinese scoring, start with total number of pieces.
        black_piece_value = board.colors["Black"]
        white_piece_value = board.colors["White"]
        
        black_score = np.sum(board.grid == black_piece_value)
        white_score = np.sum(board.grid == white_piece_value)
        logger.info(f"Black ({black_piece_value}) has {black_score} pieces on board. Added {black_score} to score.")
        logger.info(f"White ({white_piece_value}) has {white_score} pieces on board. Added {white_score} to score")

        for region in board.regions:
            if np.isnan(region.color):
                n_adjs = list(region.n_adj_pieces.values())
                # Ignore if region has equal number of adj
                if all(n_adjs[0] == n_adj for n_adj in n_adjs) and len(n_adjs) > 1:
                    logger.info(f"Dame/seki territory. Ignored.")
                    logger.info(f"\n{region}")
                    continue
                # Get piece with the most adjacencies to empty territory.
                piece, _ = region.n_adj_pieces.most_common(1)[0]
                if piece == black_piece_value:
                    black_score += len(region)
                    logger.info(f"Added territory of {len(region)} pieces to black's score.\n{region}")
                else:
                    white_score += len(region)
                    logger.info(f"Added territory of {len(region)} pieces to white's score.\n{region}")

        region_counts = board.region_counts
        logger.info(f"Iterated through {sum(region_counts.values())} regions. {region_counts}")
        logger.info(f"Black ({black_piece_value}): {black_score}")
        logger.info(f"White ({white_piece_value}): {white_score}")

        self.scores = {"Black": black_score, "White": white_score}
        return self

    def _score_japanese(self, board, captured: collections.Counter) -> Score:
        """
        
        """
        return self

    def score(self, board, **kwargs):
        logger.info(f"Scoring board using {self.system} scoring.")
        if self.system == "Chinese":
            self._score_chinese(board)
        else:
            if "captures" not in kwargs:
                raise Exception("No captured pieces provided.")
            self._score_japanese(board)
        
        if self.komi:
            self.scores["White"] += self.default_komi

        scores = self.declare_winner()
        print(scores)
        return scores