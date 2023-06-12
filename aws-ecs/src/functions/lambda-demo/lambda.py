import json


def handler(event, context):
    print(event)

    try:
        return response_handler('Hello World', 200)

    except Exception as e:
        print(e)
        return response_handler('Internal Server Error', 500)


def response_handler(payload, status_code):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/text"
        },
        "body": payload,
        "isBase64Encoded": False
    }
