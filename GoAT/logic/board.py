from __future__ import annotations
import collections
import textwrap
import numpy as np
import igraph

from typing import Set, Tuple, List, Dict, Iterable
from dataclasses import dataclass, field
from itertools import product
from collections import Counter
from loguru import logger


@dataclass
class Region:
    id_num: int = field(init=False, default=0)
    grid: np.ndarray = field(repr=False)
    pieces: Set[Tuple[int, int]]
    color_val: str = field(init=False)

    def __post_init__(self):
        # Get random piece in region to determine color value.
        random_piece = next(iter(self.pieces))
        self.color_val = self.grid[random_piece[0], random_piece[1]]

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
    def is_dame(self) -> bool:
        if np.isnan(self.color_val) and len(self.n_adj_pieces.keys()) > 1:
            return True

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

    def __hash__(self) -> int:
        return hash((tuple(self.pieces), self.color_val, self.id_num))

    def __str__(self):
        message = f"""
            ID: {self.id_num}
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
    regions: List[Region] = field(init=False)
    graph: igraph.Graph = field(init=False)

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
    def n_rows(self) -> int:
        return self.grid.shape[0]

    @property
    def n_cols(self) -> int:
        return self.grid.shape[1]

    @property
    def dead_regions(self) -> Iterable[Region]:
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
    def region_counts(self) -> Counter:
        # Avoid nan as key.
        return Counter(
            "nan" if np.isnan(region.color_val) else region.color_val
            for region in self.regions
        )

    @property
    def seki_regions(self) -> Iterable[Region]:
        for region in self.regions:
            # If empty and has both players adjacent.
            if np.isnan(region.color_val):
                # 1st - check if legal placement.
                # 2nd - Place both pieces
                # 3rd - Reevaluate # dead groups.
                yield region
            else:
                continue

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

    def _cluster_pieces(self, loc: Tuple[int, int]) -> Iterable[Tuple[int, int]]:
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
        region_num = 1
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
            subregion = Region(self.grid, set(subregion))

            if subregion not in regions:
                subregion.id_num = region_num
                regions.append(subregion)
                region_num += 1

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
        adj_regions = []
        for n, region in enumerate(self.regions):
            for n2, region2 in enumerate(self.regions):
                # Ignore same region
                if n == n2:
                    continue

                shared_liberties = region.liberties.intersection(region2.liberties)
                adj_pieces = region.pieces.intersection(region2.adjacencies)
                adj_pieces_2 = region.adjacencies.intersection(region2.pieces)
                all_adjs = adj_pieces.union(adj_pieces_2)

                # If share liberty, join regions.
                if len(shared_liberties) != 0:
                    if region.color_val == region2.color_val:
                        # Use set to ensure no duplicates are created.
                        merged_pieces = region.pieces.union(region2.pieces)
                        joined_region = Region(self.grid, set(merged_pieces))

                        if region not in removed_regions:
                            removed_regions.append(region)
                        if region2 not in removed_regions:
                            removed_regions.append(region2)
                        if joined_region not in joined_regions:
                            joined_regions.append(joined_region)
                # If adjacent pieces
                if len(all_adjs) != 0:
                    adj_regions.append((region.id_num, region2.id_num))

        # Number removed and number joined.
        n_r, n_j = 0, 0
        for n_r, removed_region in enumerate(removed_regions, 1):
            logger.debug(f"Joining regions. Removing:\n{removed_region}")
            self.regions.remove(removed_region)
        for n_j, new_region in enumerate(joined_regions, 1):
            logger.debug(f"Joining regions. Adding:\n{new_region}")
            self.regions.append(new_region)

        # Generate graph
        self.graph = igraph.Graph(adj_regions)

        logger.debug("Finished joining regions.")
        logger.debug(f"Removed intermediate regions: {n_r}")
        logger.debug(f"Added joined regions: {n_j}")
        return self

    def grid_view(self):
        grid_view = self.grid.copy()
        for region in self.regions:
            for piece in region.pieces:
                row, col = piece
                grid_view[row, col] = region.id_num
        print(grid_view)

    def __str__(self):
        message = f"""
            Goban: {self.n_rows} x {self.n_cols}
            Pieces: {self.colors}
            Captures: {self.captures}
            Regions (Including Empty): {len(self.regions)}
        """
        return textwrap.dedent(message)
