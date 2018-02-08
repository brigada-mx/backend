from django.contrib import admin
from django.conf.urls import include, url


urlpatterns = (
    # api
    url(r'^api/', include('api.urls', namespace='api')),

    # admin
    url(r'^admin/', include(admin.site.urls)),
)
