from ninja import Schema


class ErrorOut(Schema):
    """پاسخ استاندارد خطا برای تمام endpointهای API."""

    detail: str
