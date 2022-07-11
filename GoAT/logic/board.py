from __future__ import annotations
import collections
import textwrap
import logging
import numpy as np

from typing import Set, Tuple, List, Dict, Iterable
from dataclasses import dataclass, field
from itertools import product
from collections import Counter

logger = logging.getLogger("logic")


@dataclass
class Region:
    grid: np.ndarray = field(repr=False)
    pieces: List[Tuple[int, int]]
    color_val: str = field(init=False)

    def __post_init__(self):
        self.color_val = self.grid[self.pieces[0][0], self.pieces[0][1]]

    def get_adj_pieces(self, piece: Tuple[int, int]) -> Iterable[Tuple[int, int]]:
        (row, col) = piece
        adjacencies = [(row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)]
        # Count liberties in adjacent tiles.
        for adjaceny in adjacencies:
            (adj_row, adj_col) = adjaceny
            if (0 <= adj_row < self.grid.shape[0]) and (
                0 <= adj_col < self.grid.shape[1]
            ):
                yield (adj_row, adj_col)

    @property
    def adjacencies(self) -> Set[Tuple[int, int]]:
        all_adjacencies = set()
        for piece in self.pieces:
            for adj_piece in self.get_adj_pieces(piece):
                # Avoid counting pieces within region.
                if adj_piece not in self.pieces:
                    all_adjacencies.add(adj_piece)
        return all_adjacencies

    @property
    def liberties(self) -> Set[Tuple[int, int]]:
        all_liberties = set()
        for adj_piece in self.adjacencies:
            adj_row, adj_col = adj_piece
            if np.isnan(self.grid[adj_row, adj_col]):
                all_liberties.add(adj_piece)

        return all_liberties

    @property
    def n_adj_pieces(self) -> collections.Counter:
        adj_pieces = Counter()
        for adj_piece in self.adjacencies:
            adj_piece_type = self.grid[adj_piece[0], adj_piece[1]]
            if np.isnan(adj_piece_type):
                # Do not use NaN as a dict key as NaN not equal to itself.
                adj_pieces["nan"] += 1
            else:
                adj_pieces[adj_piece_type] += 1

        return adj_pieces

    @property
    def is_dead(self) -> bool:
        if len(self.liberties) <= 1:
            return True
        else:
            return False

    @property
    def is_on_border(self) -> bool:
        n_rows = self.grid.shape[0]
        n_cols = self.grid.shape[1]
        if any(
            piece[0] in [0, n_rows - 1] or piece[1] in [0, n_cols - 1]
            for piece in self.pieces
        ):
            return True
        else:
            return False

    def __iter__(self):
        return iter(self.pieces)

    def __len__(self):
        return len(self.pieces)

    def __str__(self):
        message = f"""
            Region of {len(self.pieces)} pieces of {self.color_val}.
            Number of liberties: {len(self.liberties)}
            Pieces: {self.pieces}
            On border: {self.is_on_border}
            Number adjacencies: {self.n_adj_pieces}
        """
        return textwrap.dedent(message)


@dataclass
class Board:
    grid: np.ndarray
    colors: Dict[str, float]
    captures: Counter[str, int]
    regions: List[List[Tuple[int, int]]] = field(init=False)

    def validate_fields(self):
        x, y = self.grid.shape
        if x != y:
            raise Exception(f"Invalid grid shape. x:{x} =/= y: {y}")
        if "Black" not in self.colors or "White" not in self.colors:
            raise Exception(f"Invalid colors in provided colors: {self.colors.keys()}")
        if self.colors.keys() != self.captures.keys():
            raise Exception(f"Invalid colors in captures: ({self.captures}).")
        if not all(isinstance(piece_val, float) for piece_val in self.colors.values()):
            raise Exception(
                f"Pieces must have an associated float value. {self.colors.values()}"
            )

    def __post_init__(self):
        self.validate_fields()

        logger.info(f"Pieces: {self.colors}")
        logger.info(f"Starting board:\n\n{self.grid}\n")

        self._get_regions()._join_nearby_regions()

    @property
    def n_rows(self):
        return self.grid.shape[0]

    @property
    def n_cols(self):
        return self.grid.shape[1]

    @property
    def dead_regions(self):
        for region in self.regions:
            # Skip empty regions.
            if np.isnan(region.color_val):
                continue

            if region.is_dead:
                yield region

    @property
    def n_dead_pieces(self) -> Counter:
        dead_pieces = Counter()
        for region in self.dead_regions:
            color = self.colors.inverse[region.color_val]
            dead_pieces[color] += len(region.pieces)
        return dead_pieces

    @property
    def region_counts(self):
        # Avoid nan as key.
        return Counter(
            "nan" if np.isnan(region.color_val) else region.color_val
            for region in self.regions
        )

    def clear_dead_regions(self) -> Board:
        logger.info("Clearing dead regions from board.")
        for region in self.dead_regions:
            region_color = self.colors.inverse[region.color_val]
            for i, piece in enumerate(region, 1):
                (row, col) = piece

                # Update captured pieces.
                self.captures[region_color] += 1

                self.grid[row, col] = np.nan
            logger.info(f"Removed {i} {region_color} pieces from board.\n{region}")

        # Update regions.
        self._get_regions()._join_nearby_regions()
        logger.debug(
            "Updated and joined adjacent board regions after clearing dead regions."
        )

        return self

    def _cluster_pieces(self, loc: Tuple[int, int]) -> Iterable:
        row, col = loc

        yield loc
        curr_piece = self.grid[row, col]
        if not col + 1 == self.n_cols:
            adj_piece = self.grid[row, col + 1]
            # Check adjacent pieces are equivalent. Then keep going to next col.
            if np.array_equal(curr_piece, adj_piece) or (
                np.isnan(curr_piece) & np.isnan(adj_piece)
            ):
                yield from self._cluster_pieces((row, col + 1))
        if not row + 1 == self.n_rows:
            adj_piece = self.grid[row + 1, col]
            if np.array_equal(curr_piece, adj_piece) or (
                np.isnan(curr_piece) & np.isnan(adj_piece)
            ):
                yield from self._cluster_pieces((row + 1, col))

    def _get_regions(self) -> Board:
        regions = []
        # Produce all separate regions by iterating through all pieces on board.
        # Then condensing intersecting regions.
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

        self.regions = regions
        logger.debug(f"Detected {len(self.regions)} total regions.")
        return self

    def _join_nearby_regions(self) -> Board:
        """
        Join regions with at least one shared liberty.

        :return self: Board instance
        """
        removed_regions = []
        joined_regions = []
        for n, region in enumerate(self.regions):
            for n2, region2 in enumerate(self.regions):
                if n != n2 and region.color_val == region2.color_val:
                    shared_liberties = region.liberties.intersection(region2.liberties)
                    if len(shared_liberties) != 0:
                        # Sort to ensure no duplicates are created.
                        merged_pieces = sorted(region.pieces + region2.pieces)
                        joined_region = Region(self.grid, list(merged_pieces))

                        if region not in removed_regions:
                            removed_regions.append(region)
                        if region2 not in removed_regions:
                            removed_regions.append(region2)
                        if joined_region not in joined_regions:
                            joined_regions.append(joined_region)

        for n_r, removed_region in enumerate(removed_regions, 1):
            logger.debug(f"Joining regions. Removing:\n{removed_region}")
            self.regions.remove(removed_region)
        for n_j, new_region in enumerate(joined_regions, 1):
            logger.debug(f"Joining regions. Adding:\n{new_region}")
            self.regions.append(new_region)
        logger.debug("Finished joining regions.")
        logger.debug(f"Removed intermediate regions: {n_r}")
        logger.debug(f"Added joined regions: {n_j}")
        return self

    def __str__(self):
        message = f"""
            Goban: {self.n_rows} x {self.n_cols}
            Pieces: {self.colors}
            Captures: {self.captures}
            Regions (Including Empty): {len(self.regions)}
        """
        return textwrap.dedent(message)
