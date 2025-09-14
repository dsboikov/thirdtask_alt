from __future__ import annotations
from typing import Iterable, List, Any
from django import template

register = template.Library()


@register.filter
def chunks(iterable: Iterable[Any], size: int) -> List[list[Any]]:
    """
    Разбивает iterable на чанки фиксированного размера.
    Пример: {{ items|chunks:4 }} -> [[i0..i3], [i4..i7], ...]
    """
    data = list(iterable)
    size = int(size) if size else 1
    return [data[i:i + size] for i in range(0, len(data), size)]
