from django.contrib import admin
from django.db.models import Avg, Count
from products.models import Category, Product, Review, ProductView


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "parent", "created_at")
    search_fields = ("name",)
    list_filter = ("parent",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "category", "price", "stock", "is_active", "avg_rating", "view_count", "created_at")
    list_filter = ("category", "is_active",)
    search_fields = ("name", "description")
    autocomplete_fields = ("category",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_avg=Avg("reviews__rating"))

    def avg_rating(self, obj):
        return round(obj._avg or 0, 2)

    avg_rating.short_description = "Средний рейтинг"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("comment", "product__name", "user__username")


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "session_key", "ip", "created_at")
    list_select_related = ("product", "user")
    date_hierarchy = "created_at"
    search_fields = ("product__name", "user__username", "session_key", "ip")
    readonly_fields = ("product", "user", "session_key", "ip", "created_at")

    def has_add_permission(self, request):  # запрет ручного добавления
        return False

    def has_change_permission(self, request, obj=None):
        return False
