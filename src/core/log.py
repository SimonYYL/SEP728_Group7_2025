import logging, sys

def setup_logging(level: str='INFO'):
    lvl=getattr(logging, level.upper(), logging.INFO)
    fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    logging.basicConfig(stream=sys.stdout, level=lvl, format=fmt)
