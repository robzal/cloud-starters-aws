

class Report(object):
    def __init__(self, client_ddb, resource_ddb=None):
        self.client_ddb = client_ddb
        self.resource_ddb = resource_ddb
