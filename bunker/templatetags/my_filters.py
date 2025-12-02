from django import template

register = template.Library()

@register.filter
def age_filter(age):
    if age is None:
        return ''
    # if 11 <= age % 100 <= 14:
    #     return 'лет'
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