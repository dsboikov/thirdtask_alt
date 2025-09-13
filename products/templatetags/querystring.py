from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs) -> str:
    """
    Возвращает querystring с заменой/удалением ключей.
    Пример: href="?{% url_replace page=2 %}"
    Чтобы удалить ключ, передайте None: {% url_replace page=None %}
    """
    request = context.get("request")
    if not request:
        return ""
    query = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()
