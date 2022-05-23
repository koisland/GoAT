import pprint
import numpy as np
from typing import Tuple, List, Dict
from dataclasses import dataclass
from itertools import product

from GoAT.logic.scoring import Score

@dataclass
class Board(Score):
    grid: np.ndarray

    def validate_fields(self):
        x, y = self.grid.shape
        if x != y:
            raise Exception(f"Invalid grid shape. x:{x} =/= y: {y}")

    def __post_init__(self):
        self.validate_fields()

    @property
    def n_rows(self):
        return self.grid.shape[0]

    @property
    def n_cols(self):
        return self.grid.shape[1]

    def dead_pieces(self):
        regions = self.regions()
        for region in regions:

            # skip empty regions
            color = self.grid[region[0][0],region[0][1]]
            if np.isnan(color):
                continue

            liberties = set()

            # Add liberties in each region.
            for piece in region:
                (row, col) = piece
                
                # Count liberties in adjacent tiles.
                if row + 1 < self.n_rows:
                    adj_piece = (row + 1, col)
                    if np.isnan(self.grid[row + 1, col]):
                        liberties.add(adj_piece)
                if row - 1 > 0:
                    adj_piece = (row - 1, col)
                    if np.isnan(self.grid[row - 1, col]):
                        liberties.add(adj_piece)
                if col + 1 < self.n_rows:
                    adj_piece = (row, col + 1)
                    if np.isnan(self.grid[row, col + 1]):
                        liberties.add(adj_piece)
                if col - 1 > 0:
                    adj_piece = (row, col - 1)
                    if np.isnan(self.grid[row, col - 1]):
                        liberties.add(adj_piece)
            
            if len(liberties) == 1 or None:
                yield region

    def _cluster_pieces(self, loc: Tuple[int, int]):
        row, col = loc

        yield loc
        curr_piece = self.grid[row, col]
        if not col + 1 == self.n_cols:
            adj_piece = self.grid[row, col +1]
            if np.array_equal(curr_piece, adj_piece) or (np.isnan(curr_piece) & np.isnan(adj_piece)):
                yield from self._cluster_pieces((row, col + 1))
        if not row + 1 == self.n_rows:
            adj_piece = self.grid[row + 1, col]
            if np.array_equal(curr_piece, adj_piece) or (np.isnan(curr_piece) & np.isnan(adj_piece)):
                yield from self._cluster_pieces((row + 1, col))

    def regions(self):
        print(self.grid)

        regions = []
        # Produce all separate regions.
        for pair in product(range(self.n_rows), range(self.n_cols)):
            subregion = {cluster for cluster in self._cluster_pieces(pair)}

            for region in regions:
                # Group regions that have connected pieces.
                if len(region.intersection(subregion)) > 0:
                    subregion = region.union(subregion)
                    regions.remove(region)

            if subregion not in regions:
                regions.append(subregion)

        sorted_regions = [sorted(list(region)) for region in regions]
        return sorted_regions
