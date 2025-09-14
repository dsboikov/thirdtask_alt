from __future__ import annotations
from django.contrib import admin
from django.db.models import Sum, F, Count, QuerySet
from django.db.models.functions import TruncDate
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from django.http import HttpRequest
from .models import Order, OrderItem
from products.models import Product, ProductView


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/orders/order/change_list.html"
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "id")
    inlines = [OrderItemInline]

    def get_urls(self) -> list:
        urls = super().get_urls()
        my = [
            path("analytics/", self.admin_site.admin_view(self.analytics_view),
                 name="orders_order_analytics"),
        ]
        return my + urls

    def analytics_view(self, request: HttpRequest) -> TemplateResponse:
        if not request.user.has_perm("orders.view_order"):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        revenue_statuses = ["paid", "shipped", "delivered"]
        orders = Order.objects.all()

        revenue = orders.filter(status__in=revenue_statuses).aggregate(total=Sum("total_price"))["total"] or 0
        orders_count = orders.count()

        # Кол-во заказов по статусам
        by_status = list(orders.values("status").annotate(c=Count("id")).order_by())

        # Топ продаж
        top_sold = list(
            OrderItem.objects.values("product__id", "product__name")
            .annotate(qty=Sum("quantity"), sum=Sum(F("price") * F("quantity")))
            .order_by("-qty")[:10]
        )

        # Просмотры
        total_views = ProductView.objects.count()
        top_viewed = list(
            Product.objects.order_by("-view_count").values("id", "name", "view_count")[:10]
        )

        # Динамика по дням (последние 14)
        from django.utils import timezone
        from datetime import timedelta
        since = timezone.now() - timedelta(days=14)
        daily = list(
            orders.filter(created_at__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(c=Count("id"), sum=Sum("total_price"))
            .order_by("day")
        )

        cm_group_name = "Content Managers"
        admins = User.objects.filter(is_superuser=True).count()
        cms = User.objects.filter(groups__name=cm_group_name).distinct().count()
        registered = User.objects.count()
        regular = max(registered - admins - cms, 0)

        anon_views = ProductView.objects.filter(user__isnull=True).count()
        cm_views = ProductView.objects.filter(user__groups__name=cm_group_name).count()
        admin_views = ProductView.objects.filter(user__is_superuser=True).count()
        user_views = total_views - anon_views - cm_views - admin_views

        context = dict(
            self.admin_site.each_context(request),
            title="Аналитика магазина",
            revenue=revenue,
            orders_count=orders_count,
            by_status=by_status,
            top_sold=top_sold,
            total_views=total_views,
            top_viewed=top_viewed,
            daily=daily,
            user_split=dict(
                registered=registered, admins=admins, cms=cms, regular=regular,
                views=dict(anon=anon_views, admins=admin_views, cms=cm_views, users=user_views),
            ),
        )
        return TemplateResponse(request, "admin/orders/analytics.html", context)

    @admin.action(description="Отметить как отправлено (для оплаченных)")
    def mark_shipped(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        queryset.filter(status="paid").update(status="shipped")

    @admin.action(description="Отменить (кроме отправленных/доставленных)")
    def mark_cancelled(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        queryset.exclude(status__in=["shipped", "delivered"]).update(status="cancelled")
