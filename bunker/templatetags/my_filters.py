from django import template
from django.utils import timezone

register = template.Library()

MONTHS_RU = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

@register.filter
def age_filter(age):
    if age is None:
        return ''
    if age % 10 == 1:
        return 'год'
    elif 2 <= age % 10 <= 4:
        return 'года'
    else:
        return 'лет'
    
@register.filter
def years_filter(year):
    if year == 1:
        return 'год'
    elif 2 <= year <= 4:
        return 'года'
    else:
        return 'лет'
    
@register.filter
def format_datetime(value):
    if not value:
        return ""
    value = timezone.localtime(value)
    return f"{value.day} {MONTHS_RU[value.month]} {value.year} {value.hour:02d}:{value.minute:02d}"