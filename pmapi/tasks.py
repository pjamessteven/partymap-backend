from pmapi.extensions import mail
import logging

def background_send_mail(to, subject, content, content_type,
                         from_=None, msg_type='unknown'):
    result = mail.send(to, subject, content, content_type, from_)
    logging.info('send.mail',
             to=to,
             subject=subject,
             status=result and 'sent' or 'failed',
             msg_type=msg_type)
    return result
