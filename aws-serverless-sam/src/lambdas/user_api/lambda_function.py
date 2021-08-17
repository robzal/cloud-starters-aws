from awslogger import logger
import base64
import boto3
from botocore.client import Config
import botocore.session
from datetime import datetime, date, timedelta
import decimal
from boto3.dynamodb.conditions import Key
import json
import mapping
import math
import models
import os


dynamodb = boto3.resource('dynamodb')
user_table = dynamodb.Table(os.environ['DDB_USER_TABLE_NAME'])
report_table = dynamodb.Table(os.environ['DDB_REPORT_TABLE_NAME'])


def get_users() -> dict:
    """Retrieves user records."""

    result = user_table.scan(
    )

    if 'Item' not in result or result['Item'] is None:
        return models.ApiResponse(404, models.ApiError("No Users found.")).get_proxy_response()

    # user = mapping.map_user(userid, result['Item'])

    return models.ApiResponse(200, result).get_proxy_response()

def get_user(userid: str) -> dict:
    """Retrieves the user record."""

    result = user_table.get_item(
        Key={ 'userid': userid },
        ProjectionExpression='userid, firstname, surname'
    )

    if 'Item' not in result or result['Item'] is None:
        return models.ApiResponse(404, models.ApiError("The specified user could not be found.")).get_proxy_response()

    # user = mapping.map_user(userid, result['Item'])

    return models.ApiResponse(200, result).get_proxy_response()

def get_reports() -> dict:
    """Retrieves the user record."""

    result = report_table.scan(
    )

    if 'Item' not in result or result['Item'] is None:
        return models.ApiResponse(404, models.ApiError("No reports found.")).get_proxy_response()

    # user = mapping.map_user(userid, result['Item'])

    return models.ApiResponse(200, result).get_proxy_response()

def delete_user(userid: str) -> dict:
    """Retrieves the user record."""

    result = user_table.get_item(
        Key={ 'userid': userid },
        ProjectionExpression='userid, firstname, surname'
    )

    if 'Item' not in result or result['Item'] is None:
        return models.ApiResponse(404, models.ApiError("The specified user could not be found.")).get_proxy_response()

    # user = mapping.map_user(userid, result['Item'])

    return models.ApiResponse(200, result).get_proxy_response()

def create_user(userid: str, user: models.User) -> dict:
    """Creates the logical profile resource, representing a subset of client, with the specified values."""

    try:
        result = user_table.update_item(
            Key={ 'userid': userid },
            UpdateExpression="set FirstName = :fn, LastName = :ln, EmailAddress = :ea, PhoneNumber = :pn, CorrespondencePreference = :cp, Active = :af, Locked = :lf, InsertDate = :cd, LastUpdated = :cd",
            ConditionExpression='attribute_not_exists(userid)',
            ExpressionAttributeValues={
                ':fn': user.first_name,
                ':ln': user.last_name,
                ':ea': user.email_address,
                ':pn': user.mobile_number
            },
            ReturnValues="UPDATED_NEW"
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return models.ApiResponse(409, models.ApiError("The specified client already exists. Use the PUT method to update the resource.")).get_proxy_response()
    
    created_profile = mapping.map_user(userid, result['Attributes'])

    return models.ApiResponse(201, created_profile).get_proxy_response()


def update_user(userid: str, user: models.User) -> dict:
    """Updates the logical profile resource, representing a subset of client, with the specified values."""

    try:
        result = user_table.update_item(
            Key={ 'ClientId': userid },
            UpdateExpression="set FirstName = :fn, LastName = :ln, EmailAddress = :ea, PhoneNumber = :pn, LastUpdated = :cd",
            ConditionExpression="attribute_exists(ClientId)",
            ExpressionAttributeValues={
                ':fn': user.first_name,
                ':ln': user.last_name,
                ':ea': user.email_address,
                ':pn': user.mobile_number,
                ':cd': '{}Z'.format(datetime.utcnow().isoformat())
            },
            ReturnValues="UPDATED_NEW"
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return models.ApiResponse(404, models.ApiError("The specified client could not be found.")).get_proxy_response()

    updated_profile = mapping.map_user(userid, result['Attributes'])

    return models.ApiResponse(200, updated_profile).get_proxy_response()


def lambda_handler(event, context):

    # Map the event to an API request
    req = models.ApiRequest(event)

    # Define API resource handler mappings
    resource_handler_map = {
        "/users": {
            "GET": lambda: get_users()
        },
        "/users/{userid}": {
            "GET": lambda: get_user(req.get_path_param('userid').get_unpadded_id()),
            "DELETE": lambda: delete_user(req.get_path_param('userid').get_unpadded_id()),
            "POST": lambda: create_user(
                req.get_path_param('userid').get_unpadded_id(),
                 models.User.from_json(req.get_body())
            ),
            "PUT": lambda: update_user(
                req.get_path_param('userid').get_unpadded_id(),
                 models.User.from_json(req.get_body())
            )
        },
        "/reports": {
            "GET": lambda: get_reports()
        }
    }

    # Attempt to get the handler for the specified resource and HTTP method
    try:
        handler = resource_handler_map[event['resource']][event['httpMethod']]
    except (KeyError):
        logger.error(
            "Unable to find handler for '{} {}'".format(event['httpMethod'], event['resource']))
        return models.ApiResponse(400, models.ApiError("The specified operation is not supported.")).get_proxy_response()

    # Return the proxy-formatted response created by the matching handler
    return handler()
