import numpy as np
from dataclasses import dataclass

@dataclass
class Score:
    SCORING_SYSTEMS = ["Japanese", "Chinese"]
    # https://senseis.xmp.net/?JapaneseCountingExample
    # https://senseis.xmp.net/?ChineseCountingExample
    system: str

    def validate_fields(self):
        if self.system not in self.SCORING_SYSTEMS:
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
