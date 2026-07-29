from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja import Router, Schema, Status
from ninja.responses import codes_4xx

from accounts.security import student_auth
from config.schemas import ErrorOut
from .models import Order
from .services import StoreError, add_course, create_order, get_cart, remove_course, simulate_payment

router = Router(tags=["Cart & Orders"])


class CartItemIn(Schema):
    course_id: int


class CheckoutIn(Schema):
    first_name: str
    last_name: str
    email: str
    phone: str
    coupon_code: str = ""


def cart_payload(user):
    cart = get_cart(user)
    items = list(cart.items.select_related("course", "course__category"))
    return {
        "id": cart.id,
        "items": [
            {
                "course_id": item.course_id,
                "code": item.course.code,
                "title": item.course.title,
                "price": item.course.price,
                "image_url": item.course.image_url,
                "category": item.course.category.name,
            }
            for item in items
        ],
        "count": len(items),
        "subtotal": sum(item.course.price for item in items),
    }


@router.get("/cart", auth=student_auth)
def read_cart(request):
    return cart_payload(request.auth)


@router.post("/cart/items", auth=student_auth, response={201: dict, codes_4xx: ErrorOut})
def add_cart_item(request, payload: CartItemIn):
    try:
        add_course(request.auth, payload.course_id)
    except StoreError as exc:
        return Status(exc.status, {"detail": exc.message})
    data = cart_payload(request.auth)
    data["message"] = "دوره به سبد خرید اضافه شد."
    return Status(201, data)


@router.delete("/cart/items/{course_id}", auth=student_auth, response={200: dict, codes_4xx: ErrorOut})
def delete_cart_item(request, course_id: int):
    try:
        remove_course(request.auth, course_id)
    except StoreError as exc:
        return Status(exc.status, {"detail": exc.message})
    data = cart_payload(request.auth)
    data["message"] = "دوره از سبد خرید حذف شد."
    return data


@router.post("/checkout", auth=student_auth, response={201: dict, codes_4xx: ErrorOut})
def checkout(request, payload: CheckoutIn):
    if len(payload.first_name.strip()) < 2 or len(payload.last_name.strip()) < 2:
        return Status(400, {"detail": "نام و نام خانوادگی معتبر نیست."})
    try:
        validate_email(payload.email.strip())
    except ValidationError:
        return Status(400, {"detail": "ایمیل معتبر نیست."})
    phone = payload.phone.strip()
    if not phone.isdigit() or not 10 <= len(phone) <= 15:
        return Status(400, {"detail": "شماره موبایل معتبر نیست."})
    try:
        order = create_order(
            request.auth,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
            coupon_code=payload.coupon_code,
        )
    except StoreError as exc:
        return Status(exc.status, {"detail": exc.message})
    return Status(201, {
        "message": "سفارش ایجاد شد و منتظر پرداخت آزمایشی است.",
        "order_number": order.number,
        "total_amount": order.total_amount,
        "status": order.status,
    })


@router.post("/orders/{order_number}/pay", auth=student_auth, response={200: dict, codes_4xx: ErrorOut})
def pay(request, order_number: str):
    try:
        order = simulate_payment(request.auth, order_number)
    except StoreError as exc:
        return Status(exc.status, {"detail": exc.message})
    return {
        "message": "پرداخت آزمایشی با موفقیت ثبت شد.",
        "order_number": order.number,
        "status": order.status,
        "reference_code": order.payment.reference_code,
        "redirect_url": f"/checkout/success/{order.number}/",
    }


@router.get("/orders", auth=student_auth)
def list_orders(request):
    orders = Order.objects.filter(user=request.auth).prefetch_related("items").select_related("payment")
    return [
        {
            "number": order.number,
            "status": order.status,
            "status_label": order.get_status_display(),
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "total_amount": order.total_amount,
            "created_at": order.created_at.isoformat(),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "items": [{"title": item.course_title, "code": item.course_code, "price": item.unit_price} for item in order.items.all()],
        }
        for order in orders
    ]
