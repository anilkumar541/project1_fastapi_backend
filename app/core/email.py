from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings

_mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

_mailer = FastMail(_mail_config)


async def send_password_reset_email(email: str, reset_url: str) -> None:
    html = f"""
    <p>You requested a password reset. Click the link below to set a new password:</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
    <p>If you did not request this, please ignore this email.</p>
    """
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=html,
        subtype=MessageType.html,
    )
    await _mailer.send_message(message)
