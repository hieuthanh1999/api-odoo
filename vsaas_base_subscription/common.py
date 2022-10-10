from enum import Enum


class Status(Enum):
    SUCCESS = 'success'
    FAILED = 'failed'


def json_response(data=None, message='', status=200):
    return {
        'data': data,
        'errorCode': status,
        'description': message
    }
