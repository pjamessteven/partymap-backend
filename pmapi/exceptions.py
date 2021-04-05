from flask import g, request
import uuid


ERROR_CODES = {
    # CODE : Message
    'AUTH_FAIL': 'Invalid credentials',
    'ACCOUNT_DISABLED': "Account is temporarily disabled. Contact info@partymap.com",
    'ACCOUNT_PENIDNG': 'Account has not been activated. Check your email!'
}


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class ErrorArgs(dict):
    """Handle gracefully missing values in error format args"""

    def __missing__(self, key):
        return key


class JSONException(Exception):
    """Custom JSON based exception.
    :param code: error code used to look up error message
    :param params: parameters to format the error code message with
    :param status_code: response status_code
    :param message: exception message - ignored if `code` is provided
    """
    code = None
    params = None
    status_code = 404
    message = ''
    details = None

    def __init__(self, message=None, code=None, params=None, status_code=None, **kwargs):
        """If `code` is provided, the the error message will be sourced from ERROR_CODES
        and formatted with values provided in the dict params (if any)."""
        Exception.__init__(self)
        if code is not None:
            self.code = code
            self.message = ERROR_CODES.get(code, '')
            if type(params) is dict:
                self.params = params
                self.message = self.message.format_map(ErrorArgs(**params))
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        if kwargs.get('details'):
            self.details = kwargs.get('details')

    def to_dict(self):
        rv = {
            'error': {
                'code': self.code,
                'message': self.message,
                # 'type': str(self.__class__.__name__),
                'request_id': g.setdefault('request_id', str(uuid.uuid4()))
            }
        }
        if self.details:
            rv['error']['details'] = self.details
        if self.params:
            rv['error']['params'] = self.params
        return rv


class InvalidContentType(JSONException):
    """
    Raised when an invalid Content-Type is provided.
    """
    pass


class LoginRequired(JSONException):
    status_code = 401
    code = 'AUTH_FAIL'

class UserDisabled(JSONException):
    status_code = 403
    code = "ACCOUNT_DISABLED"
    message = "Account is temporarily disabled. Contact info@partymap.com"

class UserPending(JSONException):
    status_code = 403
    code = "ACCOUNT_PENIDNG"
    message = "Account has not been activated. Check your email!"

class InvalidPermissions(JSONException):
    status_code = 403


class InvalidAPIRequest(JSONException):
    """
    Raised when an invalid request has been made.
    (e.g. accessed unexisting url, the schema validation did
    not pass)
    """
    status_code = 400


class InvalidRoute(JSONException):
    """Raised instead of issuing a route redirect."""
    status_code = 404


class UnprocessableEntity(JSONException):
    """Raised when a request is syntactically correct but semantically erroneous"""
    status_code = 422


class SystemError(JSONException):
    status_code = 500
    message = ("There was a server error completing your request."
               " Our team has been notified will look into it.")


class UpstreamError(JSONException):
    status_code = 502
    message = "An error occurred upstream"


class DatabaseError(JSONException):
    """
    Generic database interaction error.
    Inherit this error for all subsequent
    errors that are related to database.
    """
    pass


class DatabaseConnectionError(DatabaseError):
    status_code = 503
    message = "There was an error connecting to the database. Please try again."


class RecordNotFound(DatabaseError):
    """
    Raised when the record was not found in the database.
    """
    status_code = 404


class RecordAlreadyExists(DatabaseError):
    """
    Raised in the case of violation of a unique constraint.
    """
    status_code = 409
    message = "There was a conflict with another record."


class RecordHasDependents(DatabaseError):
    """
    Raised in the case where a record is referred to in a foreign key constraint.
    """
    status_code = 409
