import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To, MailSettings, SandBoxMode
from pmapi.exceptions import InvalidAPIRequest, SystemError
from pmapi import validate
import logging


import os
import logging
import requests
from urllib.parse import urlencode

# Assume these are defined elsewhere, similar to your existing setup
# from your_project.validation import validate
# from your_project.exceptions import InvalidAPIRequest

class Mailer:
    def __init__(self, client_id, client_secret, account_id, default_from, testing=False):
        self.client_id = client_id
        self.client_secret = client_secret
        self.account_id = account_id
        self.default_from = default_from
        self.testing = testing
        self._access_token = None # Store access token after fetching

    def _get_zoho_access_token(self, scope="ZohoMail.messages.CREATE"):
        """Fetches the Zoho Mail API access token using client credentials."""
        if self._access_token:
            return self._access_token

        token_url = "https://accounts.zoho.com.au/oauth/v2/token" # Adjust for your Zoho region

        if not self.client_id or not self.client_secret:
            raise SystemError("ZOHO Client ID or Secret missing")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": scope,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = requests.post(token_url, data=urlencode(payload), headers=headers)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()
            self._access_token = data.get("access_token")
            if not self._access_token:
                raise SystemError("Failed to fetch Zoho access token: No access_token in response")
            return self._access_token
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching Zoho access token: {e}")
            raise SystemError(f"Error fetching Zoho access token: {e}")
        except ValueError as e:
            logging.error(f"Error parsing Zoho access token response: {e}")
            raise SystemError(f"Error parsing Zoho access token response: {e}")

    def send_zoho_mail(
        self,
        to,
        subject,
        content,
        content_type="text/html",
        from_=None,
    ):
        """
        Sends an email using the Zoho Mail API.
        """
        from_address = from_ or self.default_from

        # Basic email validation (you'll need to adapt your 'validate.email'
        # or implement a simple regex/format check here if not already available)
        # try:
        #     validate.email(from_address)
        #     validate.email(to)
        # except InvalidAPIRequest:
        #     raise SystemError(f"Not a valid email address: From: {from_address}, To: {to}")

        access_token = self._get_zoho_access_token()
        url = f"https://mail.zoho.com.au/api/accounts/{self.account_id}/messages" # Adjust for your Zoho region

        email_data = {
            "fromAddress": from_address, # Must be a registered domain in Zoho
            "toAddress": to,
            "subject": subject,
            "content": content,
            "mailFormat": "html" if content_type == "text/html" else "plaintext" # Zoho uses mailFormat
        }

        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=email_data, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            response_data = response.json()
            logging.info("mail.send (Zoho)", success=True, subject=subject, response=response_data)
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending Zoho email: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Zoho error response: {e.response.text}")
            return False
        except ValueError as e:
            logging.error(f"Error parsing Zoho email response: {e}")
            return False

    # This would be your main 'send' function that dispatches to Zoho or other services
    def send(
        self,
        to,
        subject,
        content,
        content_type="text/html",
        from_=None,
    ):
        # You could add logic here to choose between SendGrid and Zoho
        # For now, it directly calls send_zoho_mail
        return self.send_zoho_mail(to, subject, content, content_type, from_)