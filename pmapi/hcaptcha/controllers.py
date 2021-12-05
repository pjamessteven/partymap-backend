from pmapi.config import BaseConfig as CONFIG
import requests


def validate_hcaptcha(token):

    # Build payload with secret key and token.
    data = {"secret": CONFIG.HCPATCHA_KEY, "response": token}

    # Make POST request with data payload to hCaptcha API endpoint.
    response = requests.post(url="https://hcaptcha.com/siteverify", data=data)

    json_data = response.json() if response and response.status_code == 200 else None

    # Parse JSON from response. Check for success or error codes.
    print(json_data)
    success = json_data["success"]
    print("success", success, json_data)
    if success is True:
        return True
    else:
        return False
