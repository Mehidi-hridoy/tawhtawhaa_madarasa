# core/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value
    



@register.filter
def intcomma(value):
    """Format number with commas"""
    try:
        value = float(value)
        return "{:,.2f}".format(value)
    except (ValueError, TypeError):
        return value