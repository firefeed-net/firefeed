from aiosmtplib import send
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone
from di_container import get_service

# Logging setup
logger = logging.getLogger("email_service.sender")
logger.setLevel(logging.INFO)


class EmailSender:
    def __init__(self):
        self.smtp_config = None
        self.sender_email = None

        # Setting up Jinja2 for template loading
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def _ensure_config(self):
        if self.smtp_config is None:
            config_obj = get_service(dict)
            self.smtp_config = {
                "server": config_obj.get('SMTP_SERVER', 'smtp.yourdomain.com'),
                "port": int(config_obj.get('SMTP_PORT', '465')),
                "email": config_obj.get('SMTP_EMAIL', 'your_email@yourdomain.com'),
                "password": config_obj.get('SMTP_PASSWORD', 'your_smtp_password'),
                "use_tls": config_obj.get('SMTP_USE_TLS', 'True').lower() == 'true'
            }
            self.sender_email = self.smtp_config["email"]

    async def send_password_reset_email(self, to_email: str, reset_token: str, language: str = "en") -> bool:
        """
        Sends email with password reset link

        Args:
            to_email (str): Recipient email
            reset_token (str): Password reset token
            language (str): Email language ('en', 'ru', 'de')

        Returns:
            bool: True if email sent successfully, False on error
        """
        self._ensure_config()
        start_ts = datetime.now(timezone.utc)
        logger.info(f"[EmailSender] Password reset email start: to={to_email} at {start_ts.isoformat()}Z")
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = self._get_reset_subject(language)
            message["From"] = self.sender_email
            message["To"] = to_email

            # Get email content from templates
            text_content = self._get_reset_text_content(reset_token, language)
            html_content = self._render_reset_html_template(reset_token, language)

            # Create email parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            # Add parts to message
            message.attach(text_part)
            message.attach(html_part)

            # Send email asynchronously with timeouts (connect/read/write 10 seconds each)
            # Use SSL for port 465, TLS for other ports
            use_ssl = self.smtp_config["port"] == 465
            use_start_tls = self.smtp_config.get("use_tls", False) and not use_ssl

            await send(
                message,
                hostname=self.smtp_config["server"],
                port=self.smtp_config["port"],
                username=self.sender_email,
                password=self.smtp_config["password"],
                start_tls=use_start_tls,
                use_tls=use_ssl,
                timeout=10,
            )

            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[EmailSender] Password reset email slow ({duration:.3f}s) to {to_email}")
            else:
                logger.info(f"[EmailSender] Password reset email sent in {duration:.3f}s to {to_email}")
            return True

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            logger.error(f"[EmailSender] Failed to send password reset email to {to_email} after {duration:.3f}s: {str(e)}")
            return False

    async def send_verification_email(self, to_email: str, verification_code: str, language: str = "en") -> bool:
        """
        Sends email with registration verification code

        Args:
            to_email (str): Recipient email
            verification_code (str): Verification code
            language (str): Email language ('en', 'ru', 'de')

        Returns:
            bool: True if email sent successfully, False on error
        """
        self._ensure_config()
        start_ts = datetime.now(timezone.utc)
        logger.info(f"[EmailSender] Verification email start: to={to_email} at {start_ts.isoformat()}Z")
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = self._get_subject(language)
            message["From"] = self.sender_email
            message["To"] = to_email

            # Get email content from templates
            text_content = self._get_text_content(verification_code, language)
            html_content = self._render_html_template(verification_code, language)

            # Create email parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            # Add parts to message
            message.attach(text_part)
            message.attach(html_part)

            # Send email asynchronously with 10 second timeout
            # Use SSL for port 465, TLS for other ports
            use_ssl = self.smtp_config["port"] == 465
            use_start_tls = self.smtp_config.get("use_tls", False) and not use_ssl

            await send(
                message,
                hostname=self.smtp_config["server"],
                port=self.smtp_config["port"],
                username=self.sender_email,
                password=self.smtp_config["password"],
                start_tls=use_start_tls,
                use_tls=use_ssl,
                timeout=10,
            )

            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[EmailSender] Verification email slow ({duration:.3f}s) to {to_email}")
            else:
                logger.info(f"[EmailSender] Verification email sent in {duration:.3f}s to {to_email}")
            return True

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            logger.error(f"[EmailSender] Failed to send verification email to {to_email} after {duration:.3f}s: {str(e)}")
            return False

    async def send_registration_success_email(self, to_email: str, language: str = "en") -> bool:
        """
        Sends email with successful registration congratulations

        Args:
            to_email (str): Recipient email
            language (str): Email language ('en', 'ru', 'de')

        Returns:
            bool: True if email sent successfully, False on error
        """
        self._ensure_config()
        start_ts = datetime.now(timezone.utc)
        logger.info(f"[EmailSender] Registration success email start: to={to_email} at {start_ts.isoformat()}Z")
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = self._get_registration_success_subject(language)
            message["From"] = self.sender_email
            message["To"] = to_email

            # Get email content from templates
            text_content = self._get_registration_success_text_content(language)
            html_content = self._render_registration_success_html_template(language)

            # Create email parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            # Add parts to message
            message.attach(text_part)
            message.attach(html_part)

            # Send email asynchronously with 10 second timeout
            # Use SSL for port 465, TLS for other ports
            use_ssl = self.smtp_config["port"] == 465
            use_start_tls = self.smtp_config.get("use_tls", False) and not use_ssl

            await send(
                message,
                hostname=self.smtp_config["server"],
                port=self.smtp_config["port"],
                username=self.sender_email,
                password=self.smtp_config["password"],
                start_tls=use_start_tls,
                use_tls=use_ssl,
                timeout=10,
            )

            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[EmailSender] Registration success email slow ({duration:.3f}s) to {to_email}")
            else:
                logger.info(f"[EmailSender] Registration success email sent in {duration:.3f}s to {to_email}")
            return True

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            logger.error(f"[EmailSender] Failed to send registration success email to {to_email} after {duration:.3f}s: {str(e)}")
            return False

    def _get_reset_subject(self, language: str) -> str:
        """Returns password reset email subject based on language"""
        subjects = {
            "en": "FireFeed - Password Reset",
            "ru": "FireFeed - Сброс пароля",
            "de": "FireFeed - Passwort zurücksetzen",
        }
        return subjects.get(language, subjects["en"])

    def _get_subject(self, language: str) -> str:
        """Returns email subject based on language"""
        subjects = {
            "en": "FireFeed - Account Verification Code",
            "ru": "FireFeed - Код подтверждения аккаунта",
            "de": "FireFeed - Konto-Verifizierungscode",
        }
        return subjects.get(language, subjects["en"])

    def _get_reset_text_content(self, reset_token: str, language: str) -> str:
        """Returns text version of password reset email"""
        reset_link = f"https://firefeed.net/reset-password/confirm/{reset_token}"
        if language == "ru":
            return f"""
FireFeed - Сброс пароля

Вы запросили сброс пароля для вашего аккаунта FireFeed.

Для сброса пароля перейдите по следующей ссылке:
{reset_link}

Эта ссылка действительна в течение 1 часа.

Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.

С уважением,
Команда FireFeed
            """.strip()
        elif language == "de":
            return f"""
FireFeed - Passwort zurücksetzen

Sie haben eine Passwort-Zurücksetzung für Ihr FireFeed-Konto angefordert.

Um Ihr Passwort zurückzusetzen, klicken Sie auf den folgenden Link:
{reset_link}

Dieser Link ist 1 Stunde gültig.

Wenn Sie keine Passwort-Zurücksetzung angefordert haben, ignorieren Sie diese E-Mail bitte.

Mit freundlichen Grüßen,
FireFeed Team
            """.strip()
        else:
            return f"""
FireFeed - Password Reset

You have requested a password reset for your FireFeed account.

To reset your password, click the following link:
{reset_link}

This link is valid for 1 hour.

If you did not request a password reset, please ignore this email.

Best regards,
FireFeed Team
            """.strip()

    def _get_text_content(self, verification_code: str, language: str) -> str:
        """Returns text version of email"""
        if language == "ru":
            return f"""
Добро пожаловать в FireFeed!

Ваш код подтверждения регистрации: {verification_code}

Пожалуйста, введите этот код на странице регистрации для завершения процесса.

С уважением,
Команда FireFeed
            """.strip()
        elif language == "de":
            return f"""
Willkommen bei FireFeed!

Ihr Konto-Verifizierungscode lautet: {verification_code}

Bitte geben Sie diesen Code auf der Registrierungsseite ein, um den Vorgang abzuschließen.

Mit freundlichen Grüßen,
FireFeed Team
            """.strip()
        else:
            return f"""
Welcome to FireFeed!

Your account verification code is: {verification_code}

Please enter this code on the registration page to complete the process.

Best regards,
FireFeed Team
            """.strip()

    def _render_reset_html_template(self, reset_token: str, language: str) -> str:
        """Renders password reset HTML template using Jinja2"""
        # Define template file name
        template_files = {
            "en": "password_reset_email_en.html",
            "ru": "password_reset_email_ru.html",
            "de": "password_reset_email_de.html",
        }

        template_name = template_files.get(language, template_files["en"])

        try:
            # Load and render template
            template = self.jinja_env.get_template(template_name)
            return template.render(reset_token=reset_token, current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            # Return basic HTML content if template not found
            return self._get_fallback_reset_html_content(reset_token, language)

    def _render_html_template(self, verification_code: str, language: str) -> str:
        """Renders HTML template using Jinja2"""
        # Define template file name
        template_files = {
            "en": "verification_email_en.html",
            "ru": "verification_email_ru.html",
            "de": "verification_email_de.html",
        }

        template_name = template_files.get(language, template_files["en"])

        try:
            # Load and render template
            template = self.jinja_env.get_template(template_name)
            return template.render(verification_code=verification_code, current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            # Return basic HTML content if template not found
            return self._get_fallback_html_content(verification_code, language)

    def _get_registration_success_subject(self, language: str) -> str:
        """Returns successful registration email subject based on language"""
        subjects = {
            "en": "FireFeed - Registration Successful",
            "ru": "FireFeed - Регистрация успешна",
            "de": "FireFeed - Registrierung erfolgreich",
        }
        return subjects.get(language, subjects["en"])

    def _get_registration_success_text_content(self, language: str) -> str:
        """Returns text version of successful registration email"""
        if language == "ru":
            return f"""
FireFeed - Регистрация успешна

Поздравляем! Ваша учетная запись успешно верифицирована и активирована.

Логин: Ваш email адрес
Пароль: Был указан при регистрации

Теперь вы можете войти в свою учетную запись и начать пользоваться всеми функциями нашего сервиса новостей.

С уважением,
Команда FireFeed
            """.strip()
        elif language == "de":
            return f"""
FireFeed - Registrierung erfolgreich

Herzlichen Glückwunsch! Ihr Konto wurde erfolgreich verifiziert und aktiviert.

Login: Ihre E-Mail-Adresse
Passwort: Wie bei der Registrierung angegeben

Sie können sich jetzt in Ihr Konto einloggen und alle Funktionen unseres Nachrichtendienstes nutzen.

Mit freundlichen Grüßen,
FireFeed Team
            """.strip()
        else:
            return f"""
FireFeed - Registration Successful

Congratulations! Your account has been successfully verified and activated.

Login: Your email address
Password: As specified during registration

You can now log in to your account and start using all the features of our news service.

Best regards,
FireFeed Team
            """.strip()

    def _render_registration_success_html_template(self, language: str) -> str:
        """Renders successful registration HTML template using Jinja2"""
        # Define template file name
        template_files = {
            "en": "registration_success_email_en.html",
            "ru": "registration_success_email_ru.html",
            "de": "registration_success_email_de.html",
        }

        template_name = template_files.get(language, template_files["en"])

        try:
            # Load and render template
            template = self.jinja_env.get_template(template_name)
            return template.render(current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            # Return basic HTML content if template not found
            return self._get_fallback_registration_success_html_content(language)

    def _get_fallback_html_content(self, verification_code: str, language: str) -> str:
        """Returns basic HTML content if template not found"""
        year = datetime.now().year
        if language == "ru":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Подтверждение регистрации</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>
        
        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Добро пожаловать в FireFeed!</h2>
            
            <p>Спасибо за регистрацию в нашем сервисе новостей.</p>
            
            <div style="background-color: #fff; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;">Ваш код подтверждения:</p>
                <h3 style="margin: 10px 0; font-size: 32px; color: #ff6b35; letter-spacing: 3px;">{verification_code}</h3>
                <p style="margin: 0; font-size: 14px; color: #999;">Введите этот код на странице регистрации</p>
            </div>
            
            <p>Если вы не регистрировались в FireFeed, просто проигнорируйте это письмо.</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
        elif language == "de":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Konto-Verifizierung</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>
        
        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Willkommen bei FireFeed!</h2>
            
            <p>Vielen Dank für Ihre Registrierung bei unserem Nachrichtendienst.</p>
            
            <div style="background-color: #fff; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;">Ihr Verifizierungscode:</p>
                <h3 style="margin: 10px 0; font-size: 32px; color: #ff6b35; letter-spacing: 3px;">{verification_code}</h3>
                <p style="margin: 0; font-size: 14px; color: #999;">Geben Sie diesen Code auf der Registrierungsseite ein</p>
            </div>
            
            <p>Wenn Sie sich nicht bei FireFeed registriert haben, ignorieren Sie bitte diese E-Mail.</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. Alle Rechte vorbehalten.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
        else:
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Account Verification</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>
        
        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Welcome to FireFeed!</h2>
            
            <p>Thank you for registering with our news service.</p>
            
            <div style="background-color: #fff; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;">Your verification code:</p>
                <h3 style="margin: 10px 0; font-size: 32px; color: #ff6b35; letter-spacing: 3px;">{verification_code}</h3>
                <p style="margin: 0; font-size: 14px; color: #999;">Enter this code on the registration page</p>
            </div>
            
            <p>If you didn't register with FireFeed, please ignore this email.</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """.strip()

    def _get_fallback_reset_html_content(self, reset_token: str, language: str) -> str:
        """Returns basic HTML content for password reset if template not found"""
        year = datetime.now().year
        reset_link = f"https://firefeed.net/reset-password/confirm/{reset_token}"
        if language == "ru":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Сброс пароля</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>

        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Сброс пароля</h2>

            <p>Вы запросили сброс пароля для вашего аккаунта FireFeed.</p>

            <div style="background-color: #fff; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;">Для сброса пароля нажмите на кнопку:</p>
                <a href="{reset_link}" style="display: inline-block; background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; font-weight: bold;">Сбросить пароль</a>
                <p style="margin: 10px 0; font-size: 14px; color: #999;">Ссылка действительна 1 час</p>
            </div>

            <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
        elif language == "de":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Passwort zurücksetzen</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>

        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Passwort zurücksetzen</h2>

            <p>Sie haben eine Passwort-Zurücksetzung für Ihr FireFeed-Konto angefordert.</p>

            <div style="background-color: #fff; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;">Klicken Sie auf die Schaltfläche, um Ihr Passwort zurückzusetzen:</p>
                <a href="{reset_link}" style="display: inline-block; background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; font-weight: bold;">Passwort zurücksetzen</a>
                <p style="margin: 10px 0; font-size: 14px; color: #999;">Link ist 1 Stunde gültig</p>
            </div>

            <p>Wenn Sie keine Passwort-Zurücksetzung angefordert haben, ignorieren Sie bitte diese E-Mail.</p>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. Alle Rechte vorbehalten.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
        else:
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Password Reset</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>

        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Password Reset</h2>

            <p>You have requested a password reset for your FireFeed account.</p>

            <div style="background-color: #fff; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;">Click the button below to reset your password:</p>
                <a href="{reset_link}" style="display: inline-block; background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; font-weight: bold;">Reset Password</a>
                <p style="margin: 10px 0; font-size: 14px; color: #999;">Link is valid for 1 hour</p>
            </div>

            <p>If you did not request a password reset, please ignore this email.</p>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """.strip()

    def _get_fallback_registration_success_html_content(self, language: str) -> str:
        """Returns basic HTML content for successful registration if template not found"""
        year = datetime.now().year
        if language == "ru":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Регистрация успешна</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>

        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Добро пожаловать в FireFeed!</h2>

            <p>Поздравляем! Ваша учетная запись успешно верифицирована и активирована.</p>

            <div style="background-color: #fff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;"><strong>Логин:</strong> Ваш email адрес</p>
                <p style="margin: 10px 0 0 0; font-size: 16px; color: #666;"><strong>Пароль:</strong> Был указан при регистрации</p>
            </div>

            <p>Теперь вы можете войти в свою учетную запись и начать пользоваться всеми функциями нашего сервиса новостей.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://firefeed.net/login" style="display: inline-block; background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Войти в учетную запись</a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
        elif language == "de":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Registrierung erfolgreich</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>

        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Willkommen bei FireFeed!</h2>

            <p>Herzlichen Glückwunsch! Ihr Konto wurde erfolgreich verifiziert und aktiviert.</p>

            <div style="background-color: #fff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;"><strong>Login:</strong> Ihre E-Mail-Adresse</p>
                <p style="margin: 10px 0 0 0; font-size: 16px; color: #666;"><strong>Passwort:</strong> Wie bei der Registrierung angegeben</p>
            </div>

            <p>Sie können sich jetzt in Ihr Konto einloggen und alle Funktionen unseres Nachrichtendienstes nutzen.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://firefeed.net/login" style="display: inline-block; background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">In Ihr Konto einloggen</a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. Alle Rechte vorbehalten.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
        else:
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FireFeed - Registration Successful</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ff6b35;">🔥 FireFeed</h1>
        </div>

        <div style="background-color: #f9f9f9; padding: 30px; border-radius: 10px; border-left: 4px solid #ff6b35;">
            <h2 style="color: #333; margin-top: 0;">Welcome to FireFeed!</h2>

            <p>Congratulations! Your account has been successfully verified and activated.</p>

            <div style="background-color: #fff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; color: #666;"><strong>Login:</strong> Your email address</p>
                <p style="margin: 10px 0 0 0; font-size: 16px; color: #666;"><strong>Password:</strong> As specified during registration</p>
            </div>

            <p>You can now log in to your account and start using all the features of our news service.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://firefeed.net/login" style="display: inline-block; background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Log In to Your Account</a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© {year} FireFeed. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """.strip()


# Create global sender instance
email_sender = EmailSender()


# Convenient function for sending email
async def send_verification_email(to_email: str, verification_code: str, language: str = "en") -> bool:
    """
    Convenient function for sending email with verification code

    Args:
        to_email (str): Recipient email
        verification_code (str): Verification code
        language (str): Email language ('en', 'ru', 'de')

    Returns:
        bool: True if email sent successfully, False on error
    """
    return await email_sender.send_verification_email(to_email, verification_code, language)


async def send_password_reset_email(to_email: str, reset_token: str, language: str = "en") -> bool:
    """
    Convenient function for sending email with password reset link

    Args:
        to_email (str): Recipient email
        reset_token (str): Password reset token
        language (str): Email language ('en', 'ru', 'de')

    Returns:
        bool: True if email sent successfully, False on error
    """
    return await email_sender.send_password_reset_email(to_email, reset_token, language)


async def send_registration_success_email(to_email: str, language: str = "en") -> bool:
    """
    Convenient function for sending email with successful registration congratulations

    Args:
        to_email (str): Recipient email
        language (str): Email language ('en', 'ru', 'de')

    Returns:
        bool: True if email sent successfully, False on error
    """
    return await email_sender.send_registration_success_email(to_email, language)
