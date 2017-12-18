from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from api import views

urlpatterns = [
    url(r'^$', views.api_root),

    url(r'^states/$', views.StateList.as_view(), name="state-list"),
    url(r'^municipalities/$', views.MunicipalityList.as_view(), name="municipality-list"),

    url(r'^localities/$', views.LocalityList.as_view(), name="locality-list"),
    url(r'^localities/(?P<cvegeo>[0-9]+)/$', views.LocalityDetail.as_view(), name="locality-detail"),

    url(r'^actions/$', views.ActionList.as_view(), name='action-list'),
    url(r'^actions/(?P<pk>[0-9]+)/log/$', views.ActionLogList.as_view(), name='action-log'),

    url(r'^organizations/$', views.OrganizationList.as_view(), name="organization-list"),
    url(r'^organizations/(?P<pk>[0-9]+)/$', views.OrganizationDetail.as_view(), name="organization-detail"),
]

# allow API to parse and return many different formats, not just default JSON
urlpatterns = format_suffix_patterns(urlpatterns)
