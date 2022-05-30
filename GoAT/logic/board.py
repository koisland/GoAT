import pprint
import numpy as np
from typing import Tuple, List, Dict, Iterable
from dataclasses import dataclass, field
from itertools import product

from GoAT.logic.scoring import Score

@dataclass
class Region:
    grid: np.ndarray = field(repr=False)
    pieces: List[Tuple[int, int]]
    color: str = field(init=False)

    def __post_init__(self):
        self.color = self.grid[self.pieces[0][0], self.pieces[0][1]]

    @property
    def n_liberties(self):
        liberties = set()
        for piece in self.pieces:
            (row, col) = piece
            
            # Count liberties in adjacent tiles.
            if row + 1 < self.grid.shape[0]:
                adj_piece = (row + 1, col)
                if np.isnan(self.grid[row + 1, col]):
                    liberties.add(adj_piece)
            if row - 1 > 0:
                adj_piece = (row - 1, col)
                if np.isnan(self.grid[row - 1, col]):
                    liberties.add(adj_piece)
            if col + 1 < self.grid.shape[1]:
                adj_piece = (row, col + 1)
                if np.isnan(self.grid[row, col + 1]):
                    liberties.add(adj_piece)
            if col - 1 > 0:
                adj_piece = (row, col - 1)
                if np.isnan(self.grid[row, col - 1]):
                    liberties.add(adj_piece)

        return len(liberties)

    @property
    def is_dead(self) -> bool:
        if self.n_liberties <= 1:
            return True
        else:
            return False
    
    @property
    def is_on_border(self) -> bool:
        if any(piece[0] in [0, self.n_rows] or piece[1] in [0, self.n_cols] for piece in self.region):
            return True
        else:
            return False
    
    def __iter__(self):
        return iter(self.pieces)

    def __str__(self):
        return f"Region of {len(self.pieces)} pieces of {self.color}."


@dataclass
class Board(Score):
    grid: np.ndarray
    colors: Dict[int, str]
    regions: List[List[Tuple[int, int]]] = field(init=False)

    def validate_fields(self):
        x, y = self.grid.shape
        if x != y:
            raise Exception(f"Invalid grid shape. x:{x} =/= y: {y}")

    def __post_init__(self):
        self.validate_fields()

        self.regions = self._get_regions()

    @property
    def n_rows(self):
        return self.grid.shape[0]

    @property
    def n_cols(self):
        return self.grid.shape[1]

    @property
    def dead_regions(self):
        for region in self.regions:
            if np.isnan(region.color):
                continue

            if region.is_dead:
                yield region

    def _cluster_pieces(self, loc: Tuple[int, int]) -> Iterable:
        row, col = loc

        yield loc
        curr_piece = self.grid[row, col]
        if not col + 1 == self.n_cols:
            adj_piece = self.grid[row, col +1]
            # Check adjacent pieces ar equivalent. Then keep going to next col.
            if np.array_equal(curr_piece, adj_piece) or (np.isnan(curr_piece) & np.isnan(adj_piece)):
                yield from self._cluster_pieces((row, col + 1))
        if not row + 1 == self.n_rows:
            adj_piece = self.grid[row + 1, col]
            if np.array_equal(curr_piece, adj_piece) or (np.isnan(curr_piece) & np.isnan(adj_piece)):
                yield from self._cluster_pieces((row + 1, col))

    def _get_regions(self):
        regions = []
        # Produce all separate regions by iterating through all pieces on board, then condensing intersecting regions.
        for pair in product(range(self.n_rows), range(self.n_cols)):
            subregion = {cluster for cluster in self._cluster_pieces(pair)}

            for i, region in enumerate(regions):
                # Group regions that have connected pieces.
                region_pieces = set(region.pieces)
                if len(region_pieces.intersection(subregion)) > 0:
                    subregion = region_pieces.union(subregion)
                    # Remove subregions that make up larger regions
                    regions.pop(i)
            
            # Init subregion as Region obj.
            subregion = Region(self.grid, list(subregion))

            if subregion not in regions:
                regions.append(subregion)

        return regions
