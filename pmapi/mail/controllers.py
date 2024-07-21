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
        "support_email": "info@partymap.com",
        "user_username": user.username,
        "year": datetime.now().year,
        "domain_business_name": "PartyMap",
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
        "support_email": "info@partymap.com",
        "user_username": user.username,
        "year": datetime.now().year,
        "domain_business_name": "PartyMap",
    }
    content = render_template(template, **context)
    return send_mail(
        to=user.email,
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="verify.email",
    )


def send_password_reset_email(user, action_id):
    template = "email/reset_password.html"
    subject = "Reset your PartyMap password"
    # XXX make dynamic
    reset_pw_url = "https://partymap.com/reset_password/{email}/{action_id}".format(
        email=user.email, action_id=action_id
    )
    context = {
        "static_reset_password_url": reset_pw_url,
        # "static_reset_password_url": user.domain.url_for(
        #     'users.UserPasswordResetResource',
        #     user_identifier=user.username,
        #     action_id=action_id),
        "support_email": "info@partymap.com",
        "static_support_url": "mailto:info@partymap.com",
        "user_username": user.username,
        "year": datetime.now().year,
        "domain_business_name": "PartyMap",
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


def send_new_event_notification(event, username="anon"):
    template = "email/new_event.html"
    subject = "New event submitted by " + username

    context = {
        "event_id": event.id,
        "event_name": event.name,
        "creator_username": username,
        "year": datetime.now().year,
        "domain_business_name": "PartyMap",
    }

    content = render_template(template, **context)
    return send_mail(
        to=current_app.config["SUPPORT_EMAIL"],
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="report.notification",
    )


def send_report_notification_email(report_id, message, email, username="anon"):
    template = "email/new_report.html"
    subject = "Content report submitted by " + username

    context = {
        "report_id": report_id,
        "message": message,
        "creator_email": email,
        "creator_username": username,
        "year": datetime.now().year,
        "domain_business_name": "PartyMap",
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

    from_address = None
    username = None
    if user:
        username = user.username
    if contact_email:
        from_address = contact_email
    elif user:
        from_address = user.email

    if from_address:
        subject = "New Feedback from " + from_address
    else:
        subject = "New Feedback from anon"

    context = {
        "feedback_id": feedback_id,
        "message": message,
        "contact_email": from_address,
        "creator_username": username,
        "year": datetime.now().year,
        "domain_business_name": "PartyMap",
    }

    content = render_template(template, **context)
    return send_mail(
        to=current_app.config["SUPPORT_EMAIL"],
        subject=subject,
        content=content,
        content_type="text/html",
        msg_type="feedback.notification",
    )
