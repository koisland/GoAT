import pprint
import numpy as np
import argparse
from GoAT.logic.board import Board
from GoAT.logic.scoring import Score
from GoAT.vision.loader import load_board


def main():
    ap = argparse.ArgumentParser(description="Calculate score from a Go board image.")
    ap.add_argument("-i", "--input", required=True, help = "Input image.")
    ap.add_argument("-s", "--scoring", required=True, help = "Scoring method.")
    ap.add_argument("-k", "--komi", action='store_true', help = "Apply komi.")
    args = vars(ap.parse_args())

    grid = load_board(args["input"])
    scoreboard = Score(args["scoring"], komi=args["komi"])
    board = Board(grid, {"Black": 1.0, "White": 0.0})
    board.clear_dead_regions()
    scoreboard.score(board)
    
if __name__ == "__main__":
    main()
