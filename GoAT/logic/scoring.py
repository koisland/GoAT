from __future__ import annotations
import collections
import numpy as np
import logging

from typing import Dict
from collections import Counter
from dataclasses import dataclass, field

from .board import Board

logger = logging.getLogger("logic")

SCORING_SYSTEMS = ["Japanese", "Chinese"]


@dataclass
class Score:

    system: str
    komi: bool = True
    scores: Dict[str, int] = field(init=False)

    def validate_fields(self):
        if self.system not in SCORING_SYSTEMS:
            raise Exception("Invalid scoring system.")

    def __post_init__(self):
        self.scores = Counter()
        self.validate_fields()

    @property
    def default_komi(self) -> float:
        """
        Set default komi for scoring methods
        https://senseis.xmp.net/?Komi

        """
        komi = {"Chinese": 7.5, "Japanese": 6.5}
        return komi[self.system]

    def declare_winner(self) -> Dict[str, int]:
        """
        Display log message and return scores.
        Assumes komi has already been added.

        :return: scores for each group
        """
        if self.scores["Black"] == self.scores["White"]:
            logger.info(f"Tie game. {self.scores}\n")
        if self.scores["Black"] > self.scores["White"]:
            logger.info(f"Black wins. {self.scores}\n")
        else:
            logger.info(f"White wins. {self.scores}\n")

        return self.scores

    def _calculate_score(self, board: Board, captured: collections.Counter) -> Score:
        """
        Score goban with Japanese (territory) or Chinese (area) method.
        Source:
            - https://senseis.xmp.net/?JapaneseCountingExample
            - https://senseis.xmp.net/?ChineseCountingExample
        :param board: Board instance
        :param capture: Captured pieces

        :return: Score
        """
        black_piece_value = board.colors["Black"]
        white_piece_value = board.colors["White"]

        if self.system == "Japanese":
            # Subtract territory from group based on number of captured pieces.
            self.scores["Black"] -= captured["Black"]
            self.scores["White"] -= captured["White"]

            logger.info(
                f"Black ({black_piece_value}) has lost {captured['Black']} pieces."
            )
            logger.info(f"Removed {captured['Black']} to black's score.")

            logger.info(
                f"White ({white_piece_value}) has lost {captured['White']} pieces."
            )
            logger.info(f"Removed {captured['White']} to white's score")

        else:
            self.scores["Black"] += np.sum(board.grid == black_piece_value)
            self.scores["White"] += np.sum(board.grid == white_piece_value)

            logger.info(
                f"Black ({black_piece_value}) has {self.scores['Black']} pieces on board."
            )
            logger.info(f"Added {self.scores['Black']} to black's score.")

            logger.info(
                f"White ({white_piece_value}) has {self.scores['White']} pieces on board."
            )
            logger.info(f"Added {self.scores['White']} to white's score")

        for region in board.regions:
            if np.isnan(region.color_val):
                n_adjs = list(region.n_adj_pieces.values())
                # Ignore if region has equal number of adj
                if all(n_adjs[0] == n_adj for n_adj in n_adjs) and len(n_adjs) > 1:
                    logger.info("Dame/seki territory. Ignored.")
                    logger.info(f"\n{region}")
                    continue
                # Get piece with the most adjacencies to empty territory.
                piece, _ = region.n_adj_pieces.most_common(1)[0]
                if piece == black_piece_value:
                    self.scores["Black"] += len(region)
                    logger.info(
                        f"Added territory of {len(region)} pieces to black's score.\n"
                    )
                    logger.info(f"{region}")
                else:
                    self.scores["White"] += len(region)
                    logger.info(
                        f"Added territory of {len(region)} pieces to white's score.\n"
                    )
                    logger.info(f"{region}")

        region_counts = board.region_counts
        logger.info(
            f"Iterated through {sum(region_counts.values())} regions. {region_counts}"
        )
        logger.info(f"Black ({black_piece_value}): {self.scores['Black']}")
        logger.info(f"White ({white_piece_value}): {self.scores['White']}")

        return self

    def score(self, board: Board, **kwargs):
        logger.info(f"Scoring board using {self.system} scoring.")
        if self.system == "Japanese" and "captured" not in kwargs:
            raise Exception("No captured pieces provided.")

        # Calculate scores with given method.
        self._calculate_score(board, captured=kwargs["captured"])

        # Add komi if desired.
        if self.komi:
            self.scores["White"] += self.default_komi

        scores = self.declare_winner()
        print(scores)
        return scores
