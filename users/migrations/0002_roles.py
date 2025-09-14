from django.db import migrations

def setup_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    cm_group, _ = Group.objects.get_or_create(name="Content Managers")

    # Разрешения на продукты/категории/отзывы
    models_perms = [
        ("products", "category"),
        ("products", "product"),
        ("products", "review"),
    ]
    perms_codenames = ["add", "change", "delete", "view"]

    for app_label, model in models_perms:
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            continue
        for cod in perms_codenames:
            perm = Permission.objects.filter(content_type=ct, codename=f"{cod}_{model}").first()
            if perm:
                cm_group.permissions.add(perm)

    # Разрешить просматривать заказы (но не менять)
    try:
        ct_order = ContentType.objects.get(app_label="orders", model="order")
        view_order = Permission.objects.filter(content_type=ct_order, codename="view_order").first()
        if view_order:
            cm_group.permissions.add(view_order)
    except ContentType.DoesNotExist:
        pass

def teardown_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Content Managers").delete()

class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_profile"),
        ("products", "0002_view_tracking"),
        ("orders", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(setup_groups, teardown_groups),
    ]
