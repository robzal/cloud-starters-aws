import json
import logging


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

logger = logging.getLogger()
logger.setLevel('INFO')

formatter = FormatterJSON(
    '[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(levelno)s\t%(message)s\n',
    '%Y-%m-%dT%H:%M:%S'
)
# Replace the LambdaLoggerHandler formatter :
if logger.handlers:
    logger.handlers[0].setFormatter(formatter)
else:
    logger.addHandler(logging.NullHandler().setFormatter(formatter))