from celery import Celery
from pmapi.extensions import mail
from pmapi import log
import logging

celery = Celery(__name__, autofinalize=False)

@celery.task(ignore_result=True)
def background_send_mail(to, subject, content, content_type,
                         from_=None, msg_type='unknown'):
    result = mail.send(to, subject, content, content_type, from_)
    logging.info('send.mail',
             to=to,
             subject=subject,
             status=result and 'sent' or 'failed',
             msg_type=msg_type)
    return result


Learn more or give us feedback
import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, MailSettings, SandBoxMode
from lc.exceptions import InvalidAPIRequest, SystemError
from lc.logging import log
from lc import validate
