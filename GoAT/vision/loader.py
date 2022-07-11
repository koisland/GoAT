import cv2
import statistics
import imutils
import logging
import numpy as np
from typing import Tuple, List, Dict, Iterator, Union

logger = logging.getLogger("vision")


class Piece:
    def __init__(self, cnt: np.ndarray, color: str):
        self.cnt = cnt
        self.color = color

    @property
    def x(self) -> Union[float, None]:
        try:
            return self._x
        except AttributeError:
            return None

    @x.setter
    def x(self, x_coord: float):
        self._x = x_coord

    @property
    def y(self) -> Union[float, None]:
        try:
            return self._y
        except AttributeError:
            return None

    @y.setter
    def y(self, y_coord: float):
        self._y = y_coord

    @property
    def center(self) -> Tuple[float, float]:
        M = cv2.moments(self.cnt)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        return cX, cY

    @property
    def x_px(self) -> float:
        return cv2.boundingRect(self.cnt)[0]

    @property
    def y_px(self) -> float:
        return cv2.boundingRect(self.cnt)[1]

    @property
    def w(self) -> float:
        return cv2.boundingRect(self.cnt)[2]

    @property
    def h(self) -> float:
        return cv2.boundingRect(self.cnt)[3]

    def __str__(self) -> str:
        return f"{self.color.capitalize()}: x_pos={self.x}, y_pos={self.y}"

    def __repr__(self) -> str:
        return f'Piece("{self.color}",\
            "{self.x_px}","{self.y_px}",\
            "{self.w}","{self.h}",\
            "{self.x}","{self.y}")'


# https://stackoverflow.com/a/15801233
def cluster_positions(positions, diff) -> Iterator[List]:
    """
    Cluster array value of pixel positions into groups based on difference in values.
    :param positions: pixel coordinates
    :param diff: threshold absolute difference from previous value to group by.

    :return: generator of grouped pixel positions
    """
    last_pos = None
    group = []

    for pos in sorted(positions):
        if last_pos is None or abs(pos - last_pos) <= diff:
            group.append(pos)
        else:
            yield group
            group = [pos]
        last_pos = pos

    if group:
        yield group


def get_board_size(
    black_pieces: List[Piece], white_pieces: List[Piece]
) -> Tuple[Tuple[int, int], Dict[float, int], Dict[float, int]]:
    """
    Get board size given piece contours.

    :return: Predicted board dimensions. (x, y)
    :return: Mapping of median x/y pixel positions to x/y board coordinates. {px: coord}
    """
    BOARD_DIMS = [5, 9, 13, 19]

    x_pos = set()
    y_pos = set()

    for pieces in [black_pieces, white_pieces]:
        for piece in pieces:
            cX, cY = piece.center
            x_pos.add(cX)
            y_pos.add(cY)

    # Sorted groups pixels into enumerated clusters
    x_groups = dict(enumerate(cluster_positions(x_pos, 5), 1))
    y_groups = dict(enumerate(cluster_positions(y_pos, 5), 1))

    # Find median value in clusters.
    x_positions = {
        round(statistics.median(vals), 0): grp for grp, vals in x_groups.items()
    }
    y_positions = {
        round(statistics.median(vals), 0): grp for grp, vals in y_groups.items()
    }

    # Find distance between x pixels and y_pixels to get number of positions on axis.
    x_pxls = list(x_positions.keys())
    y_pxls = list(y_positions.keys())

    x_distances = [abs(x_pxls[i] - x_pxls[i + 1]) for i in range(len(x_pxls) - 1)]
    y_distances = [abs(y_pxls[i] - y_pxls[i + 1]) for i in range(len(y_pxls) - 1)]

    median_x_distance = round(statistics.median(x_distances), 0)
    median_y_distance = round(statistics.median(y_distances), 0)

    # Divide largest px_pos by median distance to get number of intervals among dim.
    # Add 1 to account for final piece's additional pxs.
    x_dim_length = (x_pxls[-1] // median_x_distance) + 1
    y_dim_length = (y_pxls[-1] // median_y_distance) + 1

    largest_dim = max([x_dim_length, y_dim_length])

    # For highest board dimension, we fit to a board that is closest in size.
    abs_diff_dims = {dim: abs(largest_dim - dim) for dim in BOARD_DIMS}
    closest_board_dim = min(abs_diff_dims, key=abs_diff_dims.get)

    return (closest_board_dim, closest_board_dim), x_positions, y_positions


def get_pieces(img: np.ndarray) -> Tuple[List[Piece], List[Piece]]:
    """
    Get pieces from image based on thresholded contours.

    :return:  Black and white pieces as Piece objects.
    """
    # Blur image so threshold only show pieces
    blur = cv2.GaussianBlur(img, (9, 9), 0)

    _, thresh_blk = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY_INV)

    # Distance transform for a binary image:
    # - Finds distance from a pixel to the closest non empty pixel.
    # - Finds center of pieces.
    # - https://homepages.inf.ed.ac.uk/rbf/CVDICT/cvd.htm#tag435
    dist_transform = cv2.distanceTransform(thresh_blk, cv2.DIST_L2, 5)
    _, thresh_blk = cv2.threshold(
        dist_transform, 0.7 * dist_transform.max(), 255, cv2.THRESH_BINARY
    )

    # High threshold so only white pieces are turned to 0.
    _, thresh_white = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY)

    thresh_blk, thresh_white = thresh_blk.astype("uint8"), thresh_white.astype("uint8")
    contours_blk = cv2.findContours(
        thresh_blk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contours_white = cv2.findContours(
        thresh_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    contours_blk, contours_white = imutils.grab_contours(
        contours_blk
    ), imutils.grab_contours(contours_white)

    black_pieces = [Piece(cnt, "black") for cnt in contours_blk]
    white_pieces = [Piece(cnt, "white") for cnt in contours_white]
    return black_pieces, white_pieces


def load_board(img_path: str) -> np.ndarray:
    original = cv2.imread(img_path)
    logger.info(f"Initializing goban from image: {img_path}")

    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

    black_pieces, white_pieces = get_pieces(gray)

    (dim_x, dim_y), x_map, y_map = get_board_size(black_pieces, white_pieces)
    logger.info(f"Estimated dimensions of board: (x: {dim_x}, y: {dim_y})")

    # Initialize board.
    board = np.zeros((dim_x, dim_y))
    board[:] = np.nan

    piece_counter = {"black": 0, "white": 0}
    for pieces in [black_pieces, white_pieces]:
        for piece in pieces:
            symbol = 0.0 if piece.color == "white" else 1.0
            piece_counter[piece.color] += 1

            # Find closest board position based on
            # abs(x_pos - median value of mapped x_pos) to board position.
            x_diff = {x_pos: abs(x_px - piece.x_px) for x_px, x_pos in x_map.items()}
            y_diff = {y_pos: abs(y_px - piece.y_px) for y_px, y_pos in y_map.items()}

            x = min(x_diff, key=x_diff.get)
            y = min(y_diff, key=y_diff.get)

            # Update pieces
            piece.x = x
            piece.y = y

            # Place piece on board. # Board positions start at 1 so must subtract.
            board[piece.y - 1, piece.x - 1] = symbol

    logger.info(f"Placed {sum(piece_counter.values())} pieces: {piece_counter}")

    return board
