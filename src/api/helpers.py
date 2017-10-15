import json


def error_response_json(message=None, message_client=None, extra=None, error_type=None, dump_to_string=True):
    """The string returned by the function can be passed, e.g., to
    `PermissionDenied`, so that exception is a valid JSON string that can be
    parsed by clients. It also ensures that the client can always expect
    `message_client` and `extra` parameters in this JSON.
    """
    error = {'message': message, 'message_client': message_client, 'extra': extra, 'type': error_type}
    return json.dumps(error) if dump_to_string else error
