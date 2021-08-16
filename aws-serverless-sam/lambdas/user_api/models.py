from abc import ABC, abstractmethod
from datetime import datetime, date
from dateutil import tz
from dateutil.parser import isoparse
from distutils.util import strtobool
from enum import Enum
import json
import os
import re



class ApiParameter(object):
    def __init__(self, value: object):
        self.value = value

    def get_str_value(self, default_value: str = None) -> str:
        return str(self.value) if self.value is not None else default_value

    def get_str_value_list(self, default_value: list = None) -> list:
        return str(self.value).split(',') if self.value is not None else default_value        

    def get_int_value(self, default_value: int = None) -> int:
        return int(self.value) if self.value is not None else default_value

    def get_bool_value(self, default_value: bool = None) -> bool:
        return bool(strtobool(str(self.value))) if self.value is not None else default_value

    def get_date_value(self, default_value: date = None) -> date:
        if self.value is not None:
            parsed_date = isoparse(str(self.value))

            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.astimezone(tz.gettz(os.environ['TZ']))

            return parsed_date.date()

        return default_value

    def get_unpadded_id(self, default_value: str = None) -> str:
        return re.sub('^0*', '', str(self.value)) if self.value is not None else default_value


class ApiRequest(object):

    def __init__(self, lambda_event: dict):
        self.request_data = {}

        if 'pathParameters' in lambda_event and lambda_event['pathParameters'] is not None:
            self.request_data['pathParameters'] = lambda_event['pathParameters']
        else:
            self.request_data['pathParameters'] = {}

        if 'queryStringParameters' in lambda_event and lambda_event['queryStringParameters'] is not None:
            self.request_data['queryStringParameters'] = lambda_event['queryStringParameters']
        else:
            self.request_data['queryStringParameters'] = {}

        if 'body' in lambda_event and lambda_event['body'] is not None:
            self.request_data['body'] = lambda_event['body']
        else:
            self.request_data['body'] = None

    def get_path_param(self, key) -> ApiParameter:
        return ApiParameter(self.request_data['pathParameters'].get(key, None))

    def get_query_param(self, key) -> ApiParameter:
        return ApiParameter(self.request_data['queryStringParameters'].get(key, None))

    def get_body(self) -> str:
        return self.request_data['body']


class ApiPayload(ABC):
    """Abstract class used to represent a JSON API payload."""

    @ abstractmethod
    def to_dict(self) -> dict:
        pass

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ApiResponse():
    """Simple value object used for API payload mapping purposes."""

    def __init__(self, status_code: int, payload: ApiPayload):
        self.status_code = status_code
        self.payload = payload

    def get_proxy_response(self):
        """Gets the dictionary structure required for a Lambda proxy response."""

        return {
            'statusCode': self.status_code,
            'body': self.payload.to_json()
        }


class ApiError(ApiPayload):
    """Simple value object used for API payload mapping purposes."""

    def __init__(self, message: str):
        self.message = message

    def to_dict(self):
        """Creates a dictionary that matches the structure of the API payload JSON."""

        return {
            'message': self.message
        }


class User(ApiPayload):
    """Simple value object used for API payload mapping purposes."""

    def __init__(self, userid: str, first_name: str, last_name: str, email_address: str, mobile_number: str):
        self.userid = userid
        self.first_name = first_name
        self.last_name = last_name
        self.email_address = email_address
        self.mobile_number = mobile_number

    @ staticmethod
    def from_json(json_data: str):
        """Creates an instance of the value object from API payload JSON."""

        return json.loads(json_data, object_hook=lambda dct: User(
            dct.get('userId', None), dct['firstName'], dct['lastName'], dct['emailAddress'], dct["mobileNumber"]))

    def to_dict(self):
        """Creates a dictionary that matches the structure of the API payload JSON."""

        return {
            'userId': self.userid,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'emailAddress': self.email_address,
            'mobileNumber': self.mobile_number
        }

