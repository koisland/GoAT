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

    def _score_chinese():
        # Count pieces and empty regions
        pass

    def _score_japanese():
        pass

    def score(self, board: np.ndarray, **kwargs):
        pass
