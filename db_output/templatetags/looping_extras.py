# additional template tools to ensure separation of concerns, not worrying about formatting in views.py

from django import template
register = template.Library()


@register.simple_tag
def index(input_list, i):
    return input_list[i]
