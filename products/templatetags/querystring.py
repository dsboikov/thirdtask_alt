from __future__ import annotations
from typing import Any
from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context: dict[str, Any], **kwargs: Any) -> str:
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
