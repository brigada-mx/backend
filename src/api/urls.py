from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from api import views

urlpatterns = [
    url(r'^$', views.api_root),
    url(r'^actions/$', views.ActionList.as_view(), name="action-list"),
]

# allow API to parse and return many different formats, not just default JSON
urlpatterns = format_suffix_patterns(urlpatterns)
