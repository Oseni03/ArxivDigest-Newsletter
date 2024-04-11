from django import template

register = template.Library()


@register.inclusion_tag("subscription/partials/_features.html")
def list_features(features):
    features = features.split(",")
    return {"features": features}
