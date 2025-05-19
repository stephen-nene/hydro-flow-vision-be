from django.core.mail import send_mail
from django.conf import settings
import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import now   



def send_email_async(email):
    """Helper function to send email asynchronously."""
    try:
        email.send()
    except Exception as e:
        print(f"Email sending failed: {e}")  # Log error (or use logging framework)

def send_custom_email(to_email, subject, template_name, context):

    html_content = render_to_string(template_name, context)  
    text_content = f"Hi {context.get('senderName', 'User')},\n\nThis is the plain text version of your email."

    # Create the email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content, 
        from_email=settings.EMAIL_HOST_USER,  
        to=[to_email],
    )
    email.attach_alternative(html_content, "text/html")  
    email.send()
def send_welcome_email(user, activation_url):
    subject = "Welcome to Django server template!"
    to_email = user.email

    # Render HTML content
    html_content = render_to_string("emails/welcome_email.html", {
        "user": user,
        "activation_url": activation_url,
    })

    # Send the email
    email = EmailMultiAlternatives(subject="Welcome to Django Server Template!", body=html_content, from_email=settings.EMAIL_HOST_USER, to=[to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
    
def confirm_account_activation(user):
    subject = "Account Activation"
    to_email = user.email
    
    # Render HTML content
    html_content = render_to_string("emails/account_activation.html", {
        "user": user
    })

    # Send the email
    email = EmailMultiAlternatives(subject=subject, body=html_content, from_email=settings.EMAIL_HOST_USER, to=[to_email])
    email.attach_alternative(html_content, "text/html")
     # Send email in a separate thread
    email_thread = threading.Thread(target=send_email_async, args=(email,))
    email_thread.start()
    # send_email_verification(user, new_email, context)    
    
def send_email_verification(user, verification_url,new_email=None):
    # user has just chnaged their email
    subject = "Email Change Verification"
    to_email = user.email
    
    context = {
        "user": user,
        "verification_url": verification_url,
        "new_email": new_email or user.email
    }

    html_content = render_to_string("emails/email_verification.html", context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=html_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[to_email]
    )
    
    # Send the email
    email.attach_alternative(html_content, "text/html")
    # Send email in a separate thread
    email_thread = threading.Thread(target=send_email_async, args=(email,))
    email_thread.start()
    # email.send()
    
    
def send_password_reset_email(user, url):
    subject = "Reset Your Password"
    to_email = user.email

    # Render HTML content
    html_content = render_to_string("emails/reset_password.html", {
        "user": user,
        "activation_url": url,
    })

    # Send the email
    email = EmailMultiAlternatives(
        subject=subject, 
        body=html_content, 
        from_email=settings.EMAIL_HOST_USER, 
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    
def send_login_email(user_email, username):
    subject = "Login Notification"
    message = f"Hello {username},\n\nYou have successfully logged into your account."
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list)
    
def send_login_notification(user, ip, user_agent, browser, os, location_guess="Unknown"):
    subject = f"Login Notification for {user.username}"
    context = {
        "username": user.username,
        "ip": ip,
        "user_agent": user_agent,
        "browser": browser,
        "os": os,
        "time": now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": location_guess,
    }

    html_content = render_to_string("emails/login_notification.html", context)
    text_content = f"Hi {user.username},\nYou just logged in from IP {ip} using {browser} on {os}.\nIf this wasn’t you, please secure your account."

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    threading.Thread(target=send_email_async, args=(email,)).start()