import logging
import pathlib

log_dir = log_file = pathlib.Path(__file__).parents[2].joinpath("logs")
if not log_dir.exists():
    log_dir.mkdir(parents=True)

log_file = log_dir.joinpath("run.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
)

parent_logger = logging.getLogger("logic")
parent_logger.setLevel(logging.INFO)
parent_fhandler = logging.FileHandler(log_file)
parent_fhandler.setLevel(logging.WARNING)
parent_logger.addHandler(parent_fhandler)
