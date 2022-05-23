import argparse
from GoAT.logic.board import Board
from GoAT.logic.scoring import Score
from GoAT.vision.loader import load_board


def main():
    ap = argparse.ArgumentParser(description="Go image to board.")
    ap.add_argument("-i", "--input", required=True, help = "Input image.")

    args = vars(ap.parse_args())

    grid = load_board(args["input"])
    
    board = Board("Chinese", grid)
    print(list(board.dead_pieces()))

if __name__ == "__main__":
    main()
