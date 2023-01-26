import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    print ("Hello World")
    logger.info("Hello World")


if __name__ == '__main__':
    print ("Hello World")
    logger.info("Hello World")

