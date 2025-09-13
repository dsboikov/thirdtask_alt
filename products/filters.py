import django_filters
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    category_slug = django_filters.CharFilter(field_name="category__slug", lookup_expr="exact")

    class Meta:
        model = Product
        fields = ["category", "category_slug", "min_price", "max_price", "is_active"]
