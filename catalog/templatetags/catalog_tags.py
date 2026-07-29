from django import template

register = template.Library()


@register.filter
def in_set(value, values):
    try:
        return value in values
    except TypeError:
        return False


@register.filter
def toman(value):
    try:
        return f"{int(value):,} تومان"
    except (TypeError, ValueError):
        return value
