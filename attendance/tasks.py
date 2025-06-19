import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage, send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_feedback_confirmation_email(self, subject, message, user_email):
    """Автоответ пользователю о получении обращения"""
    try:
        subject = "Ваше обращение принято"
        message = "Спасибо за ваше обращение. Мы свяжемся с вами в ближайшее время."

        logger.info(f"Отправка подтверждения на {user_email}")

        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            fail_silently=False,
        )

        logger.info(f"Письмо отправлено, результат: {result}")
        return {"status": "success", "email": user_email, "message_id": result}

    except Exception as e:
        logger.error(f"Ошибка отправки: {str(e)}", exc_info=True)
        self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True)
def send_auto_reply(self, user_email, message):
    """Отправление обращения от пользователя администратору"""
    try:
        subject = "Новое обращение от пользователя"
        body = f"""
        Новое обращение от {user_email}
        Сообщение: {message}
        """

        logger.info(f"Пересылка обращения от {user_email} администратору")

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.EMAIL_HOST_USER,
            to=[settings.EMAIL_HOST_USER],
            headers={"Reply-To": user_email},
        )

        result = email.send(fail_silently=False)

        logger.info(f"Обращение переслано, результат: {result}")
        return {"status": "success", "admin_email": settings.EMAIL_HOST_USER, "message_id": result}

    except Exception as e:
        logger.error(f"Ошибка отправки администратору: {str(e)}", exc_info=True)
        self.retry(exc=e, countdown=60, max_retries=3)
