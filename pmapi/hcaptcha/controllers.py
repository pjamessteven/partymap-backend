from pmapi.config import BaseConfig as CONFIG
import requests
from flask.helpers import get_debug_flag
from pmapi import exceptions as exc

DEV_ENVIRON = get_debug_flag()

def validate_hcaptcha(token):

    if DEV_ENVIRON:
        return True
    
    # Build payload with secret key and token.
    data = {"secret": CONFIG.HCPATCHA_KEY, "response": token}

    # Make POST request with data payload to hCaptcha API endpoint.
    response = requests.post(url="https://hcaptcha.com/siteverify", data=data)

    json_data = response.json() if response and response.status_code == 200 else None

    # Parse JSON from response. Check for success or error codes.
    success = json_data["success"]
    if success is not True:
        raise exc.InvalidAPIRequest("HCaptcha not valid")
