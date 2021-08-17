import json
import logging
from sys import stdout

logger = logging.getLogger()
handler = logging.StreamHandler(stdout)
logger.addHandler(handler)
logger.setLevel('INFO')