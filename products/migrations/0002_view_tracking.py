from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="view_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="ProductView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(blank=True, default="", max_length=40)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="views", to="products.product")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                           to="auth.user")),
            ],
            options={
                "verbose_name": "Просмотр товара",
                "verbose_name_plural": "Просмотры товара",
            },
        ),
        migrations.AddIndex(
            model_name="productview",
            index=models.Index(fields=["product", "created_at"], name="products_pr_product_7c3be4_idx"),
        ),
        migrations.AddIndex(
            model_name="productview",
            index=models.Index(fields=["session_key"], name="products_pr_session_25fb20_idx"),
        ),
    ]
