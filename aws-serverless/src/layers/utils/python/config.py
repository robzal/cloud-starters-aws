import sys
import os


class Config(object):
    def __init__(self):
        self.config = {}
        self.read_os()

    def read_os(self):
        self.config['aws_region'] = os.environ.get('AWS_REGION', 'ap-southeast-2')
        self.config['aws_profile'] = os.environ.get('AWS_PROFILE', '')
