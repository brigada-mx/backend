from django.conf.urls import url
from django.views.decorators.cache import cache_page

from api import views


# `cache_page` also sets `Cache-Control: max-age=<seconds>` in response headers
urlpatterns = [
    # public endpoints
    url(r'^webhooks/kobo_submission/$', views.KoboSubmissionWebhook.as_view(), name='kobo-submission-webhook'),

    url(r'^$', views.api_root),

    url(r'^states/$', cache_page(60 * 5)(views.StateList.as_view()), name='state-list'),
    url(r'^municipalities/$', cache_page(60 * 5)(views.MunicipalityList.as_view()), name='municipality-list'),

    url(r'^localities/$', cache_page(60 * 20)(views.LocalityList.as_view()), name='locality-list'),
    url(r'^localities_search/$', views.LocalitySearch.as_view(), name='locality-list-search'),
    url(r'^localities/(?P<pk>[0-9]+)/$', views.LocalityDetail.as_view(), name='locality-detail'),

    url(r'^actions/$', views.ActionList.as_view(), name='action-list'),
    url(r'^actions/(?P<pk>[0-9]+)/$', views.ActionDetail.as_view(), name='action-detail'),
    url(r'^actions/(?P<pk>[0-9]+)/log/$', views.ActionLogList.as_view(), name='action-log'),

    url(r'^submissions/$', views.SubmissionList.as_view(), name='submission-list'),

    url(r'^organizations/$', cache_page(60 * 3)(views.OrganizationList.as_view()), name='organization-list'),
    url(r'^organizations/(?P<pk>[0-9]+)/$', views.OrganizationDetail.as_view(), name='organization-detail'),

    url(r'^establishments/$', cache_page(60 * 30)(views.EstablishmentList.as_view()), name='establishment-list'),

    # organization account endpoints
    url(r'^account/token/$', views.AccountToken.as_view(), name='account-token'),
    url(r'^account/delete_token/$', views.AccountDeleteToken.as_view(), name='account-delete-token'),
    url(r'^account/set_password/$', views.AccountSetPassword.as_view(), name='account-set-password'),
    url(r'^account/set_password_with_token/$',
        views.AccountSetPasswordWithToken.as_view(), name='account-set-password-with-token'),
    url(r'^account/send_set_password_email/$',
        views.AccountSendSetPasswordEmail.as_view(), name='account-send-set-password-email'),
    url(r'^account/me/$', views.AccountMe.as_view(), name='account-me'),

    url(r'^account/organization/$', views.AccountOrganizationRetrieveUpdate.as_view(),
        name='account-organization-retrieve-update'),
    url(r'^account/organization/reset_key/$',
        views.AccountOrganizationResetKey.as_view(), name='account-organization-reset-key'),
    url(r'^account/actions/$', views.AccountActionListCreate.as_view(), name='account-action-list-create'),
    url(r'^account/actions/(?P<pk>[0-9]+)/$',
        views.AccountActionRetrieveUpdate.as_view(), name='account-action-retrieve-update'),
    url(r'^account/actions_by_key/(?P<key>[0-9]+)/$',
        views.AccountActionRetrieveByKey.as_view(), name='account-action-retrieve-by-key'),
    url(r'^account/submissions/$', views.AccountSubmissionList.as_view(), name='account-submission-list'),
    url(r'^account/submissions/(?P<pk>[0-9]+)/$',
        views.AccountSubmissionUpdate.as_view(), name='account-submission-update'),
]
