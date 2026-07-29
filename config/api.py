from ninja import NinjaAPI

api = NinjaAPI(
    title="NersiMed Academy API",
    version="1.0.0",
    description="API پلتفرم آموزش پزشکی؛ احراز هویت Session، سبد، سفارش، پرداخت آزمایشی و مدیریت.",
    urls_namespace="nersimed_api",
)

api.add_router("/v1/auth", "accounts.api.router")
api.add_router("/v1/catalog", "catalog.api.router")
api.add_router("/v1/store", "orders.api.router")
api.add_router("/v1/core", "core.api.router")
api.add_router("/v1/admin", "dashboard.api.router")
