from django.conf.urls import url
from django.views.decorators.cache import cache_page

from api import views


# `cache_page` also sets `Cache-Control: max-age=<seconds>` in response headers
urlpatterns = [
    # internal endpoints
    url(r'^internal/organization_users/$',
        views.InternalOrganizationUserList.as_view(), name='internal-organization-user-list'),

    # public endpoints
    url(r'^webhooks/kobo_submission/$', views.KoboSubmissionWebhook.as_view(), name='kobo-submission-webhook'),

    url(r'^$', views.api_root),

    url(r'^states/$', cache_page(60 * 5)(views.StateList.as_view()), name='state-list'),
    url(r'^municipalities/$', cache_page(60 * 5)(views.MunicipalityList.as_view()), name='municipality-list'),

    url(r'^localities/$', cache_page(60 * 20)(views.LocalityList.as_view()), name='locality-list'),
    url(r'^localities_search/$', views.LocalitySearch.as_view(), name='locality-list-search'),
    url(r'^localities/(?P<pk>[0-9]+)/$', views.LocalityDetail.as_view(), name='locality-detail'),

    url(r'^actions/$', views.ActionList.as_view(), name='action-list'),
    url(r'^actions_mini/$', cache_page(60 * 3)(views.ActionMiniList.as_view()), name='action-mini-list'),
    url(r'^actions/(?P<pk>[0-9]+)/$', views.ActionDetail.as_view(), name='action-detail'),
    url(r'^actions/(?P<pk>[0-9]+)/log/$', views.ActionLogList.as_view(), name='action-log'),

    url(r'^submissions/$', views.SubmissionList.as_view(), name='submission-list'),

    url(r'^donations/$', cache_page(60 * 0.5)(views.DonationList.as_view()), name='donation-list'),

    url(r'^donors_mini/$', views.DonorMiniList.as_view(), name='donor-mini-list'),
    url(r'^donors/$', cache_page(60 * 3)(views.DonorList.as_view()), name='donor-list'),
    url(r'^donors/(?P<pk>[0-9]+)/$', cache_page(60 * 0.5)(views.DonorDetail.as_view()), name='donor-detail'),

    url(r'^organizations/$', cache_page(60 * 3)(views.OrganizationList.as_view()), name='organization-list'),
    url(r'^organizations/(?P<pk>[0-9]+)/$',
        cache_page(60 * 0.5)(views.OrganizationDetail.as_view()), name='organization-detail'),

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

    url(r'^account/organizations/$', views.AccountOrganizationCreate.as_view(), name='account-organization-create'),
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
        views.AccountSubmissionRetrieveUpdate.as_view(), name='account-submission-update'),

    url(r'^account/donations/$', views.AccountDonationCreate.as_view(), name='account-donation-create'),
    url(r'^account/donations/(?P<pk>[0-9]+)/$',
        views.AccountDonationRetrieveUpdateDestroy.as_view(), name='account-donation-retrieve-update-destroy'),

    url(r'^account/actions/(?P<pk>[0-9]+)/archive/$',
        views.AccountActionArchive.as_view(), name='account-action-archive'),
    url(r'^account/submissions/(?P<pk>[0-9]+)/archive/$',
        views.AccountSubmissionArchive.as_view(), name='account-submission-archive'),
    url(r'^account/submissions/(?P<pk>[0-9]+)/image/$',
        views.AccountSubmissionImageUpdate.as_view(), name='account-submission-image'),

    # donor account endpoints
    url(r'^donor_account/token/$', views.DonorToken.as_view(), name='donoraccount-token'),
    url(r'^donor_account/delete_token/$', views.DonorDeleteToken.as_view(), name='donoraccount-delete-token'),
    url(r'^donor_account/set_password/$', views.DonorSetPassword.as_view(), name='donoraccount-set-password'),
    url(r'^donor_account/set_password_with_token/$',
        views.DonorSetPasswordWithToken.as_view(), name='donoraccount-set-password-with-token'),
    url(r'^donor_account/send_set_password_email/$',
        views.DonorSendSetPasswordEmail.as_view(), name='donoraccount-send-set-password-email'),
    url(r'^donor_account/me/$', views.DonorMe.as_view(), name='donoraccount-me'),
    url(r'^donor_account/donors/$', views.DonorDonorCreate.as_view(), name='donor-donor-create'),
    url(r'^donor_account/donor/$', views.DonorRetrieveUpdate.as_view(), name='donoraccount-donor-retrieve-update'),
    url(r'^donor_account/donations/$', views.DonorDonationListCreate.as_view(), name='donoraccount-donation-create'),
    url(r'^donor_account/donations/(?P<pk>[0-9]+)/$',
        views.DonorDonationRetrieveUpdateDestroy.as_view(), name='donoraccount-donation-retrieve-update-destroy'),
]
