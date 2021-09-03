from flask import current_app, render_template, request
from datetime import datetime


def send_mail(to, subject, content, content_type, from_=None, msg_type="unknown"):
    """Send mail asynchronously."""
    from pmapi.tasks import background_send_mail

    background_send_mail(
        to, subject, content, content_type, from_=None, msg_type="unknown"
    )


def send_signup_verify_email(user, action_id, resend=False):
    template = "email/signup_verify_email.html"
    if resend:
        template = "email/activate_account_reminder.html"
    subject = "PartyMap account activation link"
    # XXX make dynamic
    acct_verify_url = "https://partymap.com/activate/{action_id}".format(
        action_id=action_id
    )
    context = {
        "account_activate_url": acct_verify_url,
        # "account_activate_url": user.domain.url_for('users.UserActivateResource',
        #                                             user_identifier=user.username,
        #                                             action_id=action_id),
        "login_url": "https://www.partymap.com/login",
        "support_email": "support@partymap.com",
        "user_username": user.username,
        "year": datetime.now().year,
    }
    content = render_template(template, **context)
    return send_mail(
        to=user.email,
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="verify.email",
    )


def send_change_email_address_email(user, action_id, resend=False):
    template = "email/change_email_address_email.html"

    subject = "Confirm your new email address"
    # XXX make dynamic
    change_email_url = "https://partymap.com/change_email/{action_id}".format(
        action_id=action_id
    )
    context = {
        "change_email_url": change_email_url,
        # "account_activate_url": user.domain.url_for('users.UserActivateResource',
        #                                             user_identifier=user.username,
        #                                             action_id=action_id),
        "login_url": "https://www.partymap.com/login",
        "support_email": "support@partymap.com",
        "user_username": user.username,
        "year": datetime.now().year,
    }
    content = render_template(template, **context)
    return send_mail(
        to=user.email,
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="verify.email",
    )


def send_password_reset_request(user, action_id):
    template = "email/reset_password.html"
    subject = "Reset your PartyMap password"
    # XXX make dynamic
    reset_pw_url = "https://partymap.com/password_reset/{username}/{action_id}".format(
        username=user.username, action_id=action_id
    )
    context = {
        "static_reset_password_url": reset_pw_url,
        # "static_reset_password_url": user.domain.url_for(
        #     'users.UserPasswordResetResource',
        #     user_identifier=user.username,
        #     action_id=action_id),
        "support_email": user.domain.support_email,
        "user_username": user.username,
        "year": datetime.now().year,
    }
    try:
        request_info = {
            "user_browser_name": request.user_agent.browser,
            "user_operating_system": request.user_agent.platform,
        }
    except RuntimeError:
        request_info = {
            "user_browser_name": "Unknown",
            "user_operating_system": "Unknown",
        }
    context.update(request_info)

    content = render_template(template, **context)
    return send_mail(
        to=user.email,
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="password.reset",
    )


def send_report_notification_email(report_id, description, user):
    template = "email/content_takedown.html"
    subject = "Report submitted by " + user.email

    context = {
        "report_id": report_id,
        "description": description,
        "creator_email": user.email,
        "creator_username": user.username,
    }

    content = render_template(template, **context)
    return send_mail(
        to=current_app.config["SUPPORT_EMAIL"],
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="report.notification",
    )


def send_feedback_notification_email(feedback_id, message, contact_email, user):
    template = "email/new_feedback.html"
    fromAddress = None
    username = None
    if user:
        username = user.username
    if contact_email:
        fromAddress = contact_email
    elif user:
        contact_email = user.email

    if fromAddress:
        subject = "New Feedback from " + fromAddress
    else:
        subject = "New Feedback from anon"

    context = {
        "feedback_id": feedback_id,
        "message": message,
        "contact_email": fromAddress,
        "creator_username": username,
    }

    content = render_template(template, **context)
    return send_mail(
        to=current_app.config["SUPPORT_EMAIL"],
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="report.notification",
    )
