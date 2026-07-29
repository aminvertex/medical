from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.csrf import csrf_protect
from ninja import Router, Schema, Status
from ninja.decorators import decorate_view
from ninja.responses import codes_4xx

from config.schemas import ErrorOut

from .models import ContactMessage, NewsletterSubscription

router = Router(tags=["Public Content"])


class ContactIn(Schema):
    name: str
    email: str
    subject: str
    message: str


class NewsletterIn(Schema):
    email: str


@router.post("/contact", auth=None, response={201: dict, codes_4xx: ErrorOut})
@decorate_view(csrf_protect)
def create_contact_message(request, payload: ContactIn):
    try:
        validate_email(payload.email.strip())
    except ValidationError:
        return Status(400, {"detail": "ایمیل معتبر نیست."})
    if len(payload.message.strip()) < 10:
        return Status(400, {"detail": "متن پیام باید حداقل ۱۰ نویسه باشد."})
    message = ContactMessage.objects.create(
        user=request.user if request.user.is_authenticated else None,
        name=payload.name.strip(),
        email=payload.email.strip().lower(),
        subject=payload.subject.strip(),
        message=payload.message.strip(),
    )
    return Status(201, {"message": "پیام شما با موفقیت ثبت شد.", "id": message.id})


@router.post("/newsletter", auth=None, response={200: dict, codes_4xx: ErrorOut})
@decorate_view(csrf_protect)
def subscribe_newsletter(request, payload: NewsletterIn):
    email = payload.email.strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return Status(400, {"detail": "ایمیل معتبر نیست."})
    subscription, created = NewsletterSubscription.objects.get_or_create(email=email, defaults={"is_active": True})
    if not created and not subscription.is_active:
        subscription.is_active = True
        subscription.save(update_fields=["is_active"])
    return {"message": "عضویت در خبرنامه انجام شد." if created else "این ایمیل قبلاً عضو خبرنامه بوده است."}
