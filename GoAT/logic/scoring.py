import numpy as np
from dataclasses import dataclass, field
from typing import Dict

SCORING_SYSTEMS = ["Japanese", "Chinese"]
# https://senseis.xmp.net/?JapaneseCountingExample
# https://senseis.xmp.net/?ChineseCountingExample

@dataclass
class Score:

    system: str
    scores: Dict[str, int] = field(init=False)

    def validate_fields(self):
        if self.system not in SCORING_SYSTEMS:
            raise Exception("Invalid scoring system.")

    def __post_init__(self):
        self.validate_fields()

    def _score_chinese(self):
        # Count pieces and empty regions
        pass

    def _score_japanese(self, captured: Dict[str, int]):
        """
        
        """
        pass

    def score(self, board, **kwargs):
        # For chinese, start with total number of pieces.
        black_score = np.sum(board.grid == 1.0)
        white_score = np.sum(board.grid == 0.0)

        for region in board.regions:
            if np.isnan(region.color):
                piece, _ = region.n_adj_pieces.most_common(1)[0]
                print(piece, len(region), region)
                if piece == 1.0:
                    black_score += len(region)
                else:
                    white_score += len(region)
        
        print(black_score, white_score)
