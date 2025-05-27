from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permet de récupérer un élément dans un dictionnaire ou une liste.
    Utilisation: {{ dictionary|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    elif isinstance(dictionary, list) and isinstance(key, int) and 0 <= key < len(dictionary):
        return dictionary[key]
    return None

@register.filter
def get_range(value):
    """
    Retourne une liste de nombres de 0 à value-1.
    Utilisation: {% for i in value|get_range %}
    """
    return range(value)

@register.filter
def attr(obj, attr_name):
    """
    Permet d'accéder à un attribut d'un objet.
    Utilisation: {{ object|attr:"attribute_name" }}
    """
    if hasattr(obj, attr_name):
        return getattr(obj, attr_name)
    elif isinstance(obj, dict):
        return obj.get(attr_name)
    return None

@register.filter
def add(value, arg):
    """
    Additionne value et arg.
    Utilisation: {{ value|add:arg }}
    """
    return value + arg

@register.filter
def mul(value, arg):
    """
    Multiplie value par arg.
    Utilisation: {{ value|mul:arg }}
    """
    return value * arg

@register.filter
def default(value, arg):
    """
    Retourne arg si value est None ou vide.
    Utilisation: {{ value|default:"0" }}
    """
    if value is None or value == '':
        return arg
    return value

@register.filter
def to_json(value):
    """
    Convertit un objet Python en chaîne JSON.
    Utilisation: {{ object|to_json }}
    """
    return mark_safe(json.dumps(value))

@register.simple_tag
def get_chart_color(index):
    """
    Retourne une couleur pour les graphiques en fonction de l'index.
    Utilisation: {% get_chart_color forloop.counter0 %}
    """
    colors = [
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)',
        'rgba(83, 102, 255, 0.7)',
        'rgba(40, 159, 64, 0.7)',
        'rgba(210, 199, 199, 0.7)'
    ]
    return colors[index % len(colors)]