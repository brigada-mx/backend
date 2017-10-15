from django.contrib import admin
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from webapp.landing.views import LandingView
from webapp.clients.views import ClientSignup
from webapp.users.views import LoginView
from webapp.users.decorators import admin_required, client_required

from decorator_include import decorator_include


urlpatterns = [
    url(r'^api/', include('api.urls', namespace='api')),

    # client signup
    url(r'^registro/$', csrf_exempt(ClientSignup.as_view()), name='signup'),

    # login/logout for all users
    url(r'^(?P<user_type>(admin|clientes|cuidadores))/login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),

    # client account
    url(r'^cuenta/', decorator_include(client_required, 'webapp.clients.urls', namespace='clients')),

    # admin
    url(r'^admin/', decorator_include(admin_required, 'webapp.staff.urls', namespace='staff')),
    url(r'^djadmin/', include(admin.site.urls)),

    url(r'^cuidadores/', include('webapp.nurses.urls', namespace='nurses')),

    url(r'^$', csrf_exempt(LandingView.as_view()), name='landing'),
    url(r'^accounts/', include('webapp.reservations.urls', namespace='reservations')),
    url(r'^messenger/', include('webapp.fb_messenger.urls', namespace='messenger')),
    url(r'^payments/', include('webapp.payments.urls', namespace='payments')),

    # static pages
    url(r'^terminos-y-condiciones/', TemplateView.as_view(template_name='docs/terms_and_conditions.html'),
        name='terms-and-conditions'),
    url(r'^aviso-de-privacidad/', TemplateView.as_view(template_name='docs/privacy_notice.html'),
        name='privacy-notice'),
    url(r'^terminos-y-condiciones-asociados/',
        TemplateView.as_view(template_name='docs/terms_and_conditions_nurses.html'),
        name='terms-and-conditions-nurses'),
    url(r'^aviso-de-privacidad-asociados/',
        TemplateView.as_view(template_name='docs/privacy_notice_nurses.html'),
        name='privacy-notice-nurses'),
    url(r'^chat-asistia/',
        TemplateView.as_view(template_name='clients/asistia_chat.html'),
        name='chat-asistia'),

    url(r'^faq/$', TemplateView.as_view(template_name='landing/faq.html'), name='faq'),
    url(r'^examen/', TemplateView.as_view(template_name='docs/exam.html'), name='exam'),
    url(r'^arco/', TemplateView.as_view(template_name='docs/arco.html'), name='arco'),

    url(r'^robots\.txt/', TemplateView.as_view(template_name='tools/robots.txt')),
    url(r'^sitemap\.xml/', TemplateView.as_view(template_name='tools/sitemap.xml')),
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
