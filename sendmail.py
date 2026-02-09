from django.core.mail import send_mail

send_mail(
    "Subject here",
    "Here is the message.",
    "pima62016@gmail.com",
    ["mukovivolonte@gmail.com"],
    fail_silently=False,
)