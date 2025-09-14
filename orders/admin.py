from django.contrib import admin
from django.db.models import Sum, Count, Q, F
from django.urls import path, reverse
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.contrib.auth.models import User, Group
from .models import Order, OrderItem
from products.models import Product, ProductView

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/orders/order/change_list.html"  # кастомный шаблон списка
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "id")
    inlines = [OrderItemInline]
    actions = ["mark_shipped", "mark_cancelled"]

    def get_urls(self):
        urls = super().get_urls()
        my = [
            path("analytics/", self.admin_site.admin_view(self.analytics_view), name="orders_order_analytics"),
        ]
        return my + urls

    def analytics_view(self, request):
        # ограничим доступ: нужно право просмотра заказов
        if not request.user.has_perm("orders.view_order"):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        revenue_statuses = ["paid", "shipped", "delivered"]
        orders = Order.objects.all()
        revenue = orders.filter(status__in=revenue_statuses).aggregate(total=Sum("total_price"))["total"] or 0
        orders_count = orders.count()
        by_status = orders.values("status").annotate(c=Count("id")).order_by()

        # Топ продаж (по количеству)
        top_sold = (
            OrderItem.objects.values("product__id", "product__name")
            .annotate(qty=Sum("quantity"), sum=Sum(F("price") * F("quantity")))
            .order_by("-qty")[:10]
        )

        # Просмотры товаров
        total_views = ProductView.objects.count()
        top_viewed = (
            Product.objects.values("id", "name").annotate(v=Sum("views__id")).order_by("-v")[:10]
        )
        # Для экономии запроса можно брать по view_count
        top_viewed = Product.objects.order_by("-view_count").values("id", "name", "view_count")[:10]

        # Заказы по суткам (последние 14)
        from django.utils import timezone
        from datetime import timedelta
        since = timezone.now() - timedelta(days=14)
        daily = (
            orders.filter(created_at__gte=since)
            .extra(select={"day": "date(created_at)"})
            .values("day")
            .annotate(c=Count("id"), sum=Sum("total_price"))
            .order_by("day")
        )

        # Пользователи и группы
        cm_group_name = "Content Managers"
        cm_group = Group.objects.filter(name=cm_group_name).first()
        admins = User.objects.filter(is_superuser=True).count()
        cms = User.objects.filter(groups__name=cm_group_name).distinct().count()
        registered = User.objects.count()
        regular = max(registered - admins - cms, 0)

        # Просмотры по типу пользователя
        anon_views = ProductView.objects.filter(user__isnull=True).count()
        cm_views = ProductView.objects.filter(user__groups__name=cm_group_name).count()
        admin_views = ProductView.objects.filter(user__is_superuser=True).count()
        user_views = total_views - anon_views - cm_views - admin_views

        context = dict(
            self.admin_site.each_context(request),
            title="Аналитика магазина",
            revenue=revenue,
            orders_count=orders_count,
            by_status=list(by_status),
            top_sold=list(top_sold),
            total_views=total_views,
            top_viewed=list(top_viewed),
            daily=list(daily),
            user_split=dict(
                registered=registered, admins=admins, cms=cms, regular=regular,
                views=dict(anon=anon_views, admins=admin_views, cms=cm_views, users=user_views),
            ),
        )
        return TemplateResponse(request, "admin/orders/analytics.html", context)

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        revenue = qs.filter(status__in=["paid", "shipped", "delivered"]).aggregate(total=Sum("total_price"))["total"] or 0
        items_count = OrderItem.objects.aggregate(total=Sum("quantity"))["total"] or 0
        extra = extra_context or {}
        extra.update({
            "revenue": revenue,
            "items_count": items_count,
            "analytics_url": reverse("admin:orders_order_analytics"),
        })
        return super().changelist_view(request, extra)

    def mark_shipped(self, request, queryset):
        updated = queryset.filter(status="paid").update(status="shipped")
        self.message_user(request, f"Отмечено как отправлено: {updated}")
    mark_shipped.short_description = "Отметить как отправлено (для оплаченных)"

    def mark_cancelled(self, request, queryset):
        updated = queryset.exclude(status__in=["shipped", "delivered"]).update(status="cancelled")
        self.message_user(request, f"Отменено: {updated}")
    mark_cancelled.short_description = "Отменить (кроме отправленных/доставленных)"
