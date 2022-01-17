import os
import json
import logging
from sys import stdout

class FormatterJSON(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        j = {
            'levelname': record.levelname,
            'time': '%(asctime)s.%(msecs)dZ' % dict(asctime=record.asctime, msecs=record.msecs),
            'aws_request_id': getattr(record, 'aws_request_id', '00000000-0000-0000-0000-000000000000'),
            'message': record.message,
            'module': record.module,
            'extra_data': record.__dict__.get('data', {}),
        }
        return json.dumps(j)

formatter = FormatterJSON(
    '[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(levelno)s\t%(message)s\n',
    '%Y-%m-%dT%H:%M:%S'
)

class Logger(object):
    def __init__(self):
        self.logger = logging.getLogger()

        #use INFO if no loglevel specified
        LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO')
        self.logger.setLevel(LOGLEVEL)

        # Replace the LambdaLoggerHandler formatter :
        if self.logger.handlers:
            self.logger.handlers[0].setFormatter(formatter)
        else:
            handler = logging.StreamHandler(stdout)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
