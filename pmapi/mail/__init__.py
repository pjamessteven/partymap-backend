import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To, MailSettings, SandBoxMode
from pmapi.exceptions import InvalidAPIRequest, SystemError
from pmapi import validate
import logging


class Mailer(object):
    """Mailer class to abstract the mail provider.
    Note the "init_app'd" instance 'mail' from the lc.extensions should be used."""

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        # die if not set
        self.api_key = app.config["SENDGRID_API_KEY"]
        self.default_from = app.config["SENDGRID_DEFAULT_FROM"]
        validate.email(self.default_from)
        self.testing = app.testing
        if self.testing:
            # keep a running count of successfully sent mail
            self.mail_sent = 0

        self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=self.api_key)

    def reset_mail_sent(self):
        # used by tests
        self.mail_sent = 0

    def send(
        self,
        to,
        subject,
        content,
        content_type="text/html",
        from_=None,
    ):
        return self.sendgrid_send(to, subject, content, content_type, from_)

    def sendgrid_send(self, to, subject, content, content_type="text/html", from_=None):

        from_ = from_ or self.default_from
        try:
            validate.email(from_)
        except InvalidAPIRequest:
            raise SystemError("Not a valid email address {}".format(from_))
        from_email = Email(from_)

        validate.email(to)
        to_email = To(to)

        email_content = Content(content_type, content)

        mail = Mail(from_email, to_email, subject, email_content)

        if self.testing:
            mail_settings = MailSettings()
            mail_settings.sandbox_mode = SandBoxMode(True)
            mail.mail_settings = mail_settings

        # in testing mode the success code is 200, otherwise success is 202
        rv = self.sendgrid_client.client.mail.send.post(request_body=mail.get())
        if rv.status_code >= 400:
            logging.error("mail.send", status_code=rv.status_code, error_body=rv.body)
            return False

        else:
            logging.info("mail.send", success=True, subject=subject)

        if self.testing:
            self.mail_sent += 1

        return True
