import json

COMMUNICATION_TYPE_EMAIL = 'EMAIL'
COMMUNICATION_TYPE_MAIL = 'MAIL'
COMMUNICATION_TYPE_SMS = 'SMS'
COMMUNICATION_TYPE_HTML = 'HTML'


class Config(object):

    def __init__(self, client_s3: object, config_bucket: str):
        """
        Correspondence application config

        :param client_s3: instance of s3 client
        :param config_bucket: config bucket name
        """

        self.__client_s3 = client_s3
        self.__config_bucket = config_bucket

    @property
    def client_s3(self) -> object:
        """
        Get s3 client object

        :return:
        """
        return self.__client_s3

    @property
    def config_bucket(self) -> str:
        """
        Get config bucket name

        :return:
        """
        return self.__config_bucket

    def load_config(self) -> dict:
        """
        Retrieve application config from s3 bucket

        :return: dict
        """
        response = self.client_s3.get_object(Bucket=self.config_bucket, Key='config.json')
        config = response['Body'].read().decode('utf-8')
        return json.loads(config)
