from django.contrib import admin
from django.db.models import Sum, F
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "id")
    inlines = [OrderItemInline]
    actions = ["mark_shipped", "mark_cancelled"]

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        revenue = qs.filter(status__in=["paid", "shipped", "delivered"]).aggregate(total=Sum("total_price"))[
                      "total"] or 0
        items_count = OrderItem.objects.aggregate(total=Sum("quantity"))["total"] or 0
        extra = extra_context or {}
        extra.update({"revenue": revenue, "items_count": items_count})
        return super().changelist_view(request, extra)

    def mark_shipped(self, request, queryset):
        updated = queryset.filter(status="paid").update(status="shipped")
        self.message_user(request, f"Отмечено как отправлено: {updated}")

    mark_shipped.short_description = "Отметить как отправлено (для оплаченных)"

    def mark_cancelled(self, request, queryset):
        updated = queryset.exclude(status__in=["shipped", "delivered"]).update(status="cancelled")
        self.message_user(request, f"Отменено: {updated}")

    mark_cancelled.short_description = "Отменить (кроме отправленных/доставленных)"
