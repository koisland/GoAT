import logging
import pathlib

log_dir = log_file = pathlib.Path(__file__).parents[2].joinpath("logs")
if not log_dir.exists():
    log_dir.mkdir(parents=True)

log_file = log_dir.joinpath("run.log")
log_format_str = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format=log_format_str,
)

parent_logger = logging.getLogger("vision")
parent_logger.setLevel(logging.INFO)
if not parent_logger.handlers:
    parent_logger.propagate = False
    parent_fhandler = logging.FileHandler(log_file)
    parent_fhandler.setLevel(logging.INFO)
    parent_fhandler.setFormatter(logging.Formatter(log_format_str))
    parent_logger.addHandler(parent_fhandler)
