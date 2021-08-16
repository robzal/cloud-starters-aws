from datetime import datetime, date
from distutils.util import strtobool
import models
import re


def get_obj_value(obj_fields: dict, key: str):
    return obj_fields[key] if key in obj_fields else None


def get_str_value(obj_fields: dict, key: str, default_value: str = None) -> str:
    value = get_obj_value(obj_fields, key)   
    return str(value) if value is not None else default_value


def get_bool_value(obj_fields: dict, key: str, default_value: bool = None) -> bool:
    value = get_obj_value(obj_fields, key)
    return bool(strtobool(str(value))) if value is not None else default_value


def get_date_value(obj_fields: dict, key: str, default_value: date = None) -> date:
    value = get_obj_value(obj_fields, key)
    return datetime.strptime(str(value), "%Y/%m/%d").date() if value is not None else default_value


def map_user(userid: str, obj_fields: dict) -> models.User:
    """Creates an instance of the ClientProfile value object from DynamoDB object fields (representing a subset of Client)."""

    return models.User(
            userid, 
            get_str_value(obj_fields, 'FirstName'),
            get_str_value(obj_fields, 'LastName'), 
            get_str_value(obj_fields, 'EmailAddress'), 
            get_str_value(obj_fields, 'PhoneNumber')
    )


