import argparse
import bidict
from collections import Counter

from GoAT.logic.board import Board
from GoAT.logic.scoring import Score
from GoAT.vision.loader import load_board


def main():
    ap = argparse.ArgumentParser(description="Calculate score from a Go board image.")
    ap.add_argument("-i", "--input", type=str, required=True, help="Input image.")
    ap.add_argument("-s", "--scoring", type=str, required=True, help="Scoring method.")
    ap.add_argument("-k", "--komi", action="store_true", help="Apply komi.")
    ap.add_argument(
        "-cb",
        "--cap_blk",
        type=int,
        required=False,
        default=0,
        help="Captured black stones by white.",
    )
    ap.add_argument(
        "-cw",
        "--cap_wht",
        type=int,
        required=False,
        default=0,
        help="Captured white stones by black.",
    )

    args = vars(ap.parse_args())
    grid = load_board(args["input"])

    # Add additional captured pieces if provided.
    # Otherwise, assume no pieces removed from board.
    captured_pieces = Counter({"Black": args["cap_blk"], "White": args["cap_wht"]})

    scoreboard = Score(args["scoring"], komi=args["komi"])
    board = Board(
        grid=grid,
        captures=captured_pieces,
        colors=bidict.bidict({"Black": 1.0, "White": 0.0}),
    )

    # Permanently clear dead regions and update captures.
    board.clear_dead_regions()

    # Score board and declare score.
    scoreboard.score(board)


if __name__ == "__main__":
    main()
