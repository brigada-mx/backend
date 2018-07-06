from django.conf.urls import url
from django.views.decorators.cache import cache_page

from api import views


# `cache_page` also sets `Cache-Control: max-age=<seconds>` in response headers
urlpatterns = [
    # internal endpoints
    url(r'^internal/app_versions/$',
        views.InternalAppVersionListCreate.as_view(), name='internal-app-version-list-create'),
    url(r'^internal/organization_users/$',
        views.InternalOrganizationUserList.as_view(), name='internal-organization-user-list'),
    url(r'^internal/debug/throw_exception/$',
        views.InternalDebugThrowException.as_view(), name='internal-debug-throw-exception'),
    url(r'^internal/email_notifications/$',
        views.InternalEmailNotificationListCreate.as_view(), name='internal-email-notification-list-create'),

    # public endpoints
    url(r'^$', views.api_root),

    url(r'^actions_cached/$', cache_page(60 * 60 * 6)(views.ActionList.as_view()), name='action-list-cached'),
    url(r'^volunteer_opportunities_cached/$',
        cache_page(60 * 60 * 6)(views.VolunteerOpportunityList.as_view()), name='volunteer-opportunity-list-cached'),
    url(r'^localities_with_actions/$',
        cache_page(60 * 60 * 6)(views.LocalityWithActionList.as_view()), name='locality-with-action-list'),
    url(r'^landing_metrics/$', cache_page(60 * 60 * 6)(views.LandingMetrics.as_view()), name='landing-metrics'),

    url(r'^webhooks/kobo_submission/$', views.KoboSubmissionWebhook.as_view(), name='kobo-submission-webhook'),
    url(r'^webhooks/discourse_event/$', views.DiscourseEventWebhook.as_view(), name='discourse-event-webhook'),

    url(r'^states/$', cache_page(60 * 5)(views.StateList.as_view()), name='state-list'),
    url(r'^municipalities/$', cache_page(60 * 5)(views.MunicipalityList.as_view()), name='municipality-list'),

    url(r'^localities/$', cache_page(60 * 20)(views.LocalityList.as_view()), name='locality-list'),
    url(r'^localities_search/$', views.LocalitySearch.as_view(), name='locality-list-search'),
    url(r'^localities/(?P<pk>[0-9]+)/$', views.LocalityDetail.as_view(), name='locality-detail'),

    url(r'^actions/$', views.ActionList.as_view(), name='action-list'),
    url(r'^actions_mini/$', cache_page(60 * 3)(views.ActionMiniList.as_view()), name='action-mini-list'),
    url(r'^actions/(?P<pk>[0-9]+)/$', cache_page(60 * 0.5)(views.ActionDetail.as_view()), name='action-detail'),
    url(r'^actions/(?P<pk>[0-9]+)/log/$', views.ActionLogList.as_view(), name='action-log'),

    url(r'^brigada_users/$', views.VolunteerUserCreate.as_view(), name='brigada-user-create'),

    url(r'^volunteer_opportunities/$',
        cache_page(60 * 3)(views.VolunteerOpportunityList.as_view()), name='volunteer-opportunity-list'),
    url(r'^volunteer_opportunities/(?P<pk>[0-9]+)/$',
        views.VolunteerOpportunityDetail.as_view(), name='volunteer-opportunity-detail'),
    url(r'^volunteer_applications/$',
        views.VolunteerUserApplicationCreate.as_view(), name='volunteer-user-application-create'),

    url(r'^shares/$', views.ShareListCreate.as_view(), name='share-list-create'),
    url(r'^share_set_user/$', views.ShareSetUser.as_view(), name='share-set-user'),
    url(r'^action_share/(?P<pk>[0-9]+)/$',
        cache_page(60 * 0.5)(views.ActionShare.as_view()), name='action-share'),

    url(r'^support_ticket_create/$', views.SupportTicketCreate.as_view(), name='support-ticket-create'),

    url(r'^submissions/$', views.SubmissionList.as_view(), name='submission-list'),
    url(r'^testimonials/(?P<pk>[0-9]+)/$', views.TestimonialDetail.as_view(), name='testimonial-detail'),

    url(r'^donations/$', cache_page(60 * 0.5)(views.DonationList.as_view()), name='donation-list'),

    url(r'^donors_mini/$', views.DonorMiniList.as_view(), name='donor-mini-list'),
    url(r'^donors/$', cache_page(60 * 3)(views.DonorList.as_view()), name='donor-list'),
    url(r'^donors/(?P<pk>[0-9]+)/$', cache_page(60 * 0.5)(views.DonorDetail.as_view()), name='donor-detail'),

    url(r'^organizations/$', cache_page(60 * 3)(views.OrganizationList.as_view()), name='organization-list'),
    url(r'^organizations/(?P<pk>[0-9]+)/$',
        cache_page(60 * 0.5)(views.OrganizationDetail.as_view()), name='organization-detail'),

    url(r'^establishments/$', cache_page(60 * 30)(views.EstablishmentList.as_view()), name='establishment-list'),

    # discourse endpoints
    url(r'^discourse/login/$', views.DiscourseLogin.as_view(), name='discourse-login'),
    url(r'^discourse/authenticated_login/$', views.DiscourseAuthLogin.as_view(), name='discourse-auth-login'),

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
    url(r'^account/profile_strength/$', views.AccountProfileStrength.as_view(), name='account-profile-strength'),

    url(r'^account/actions/$', views.AccountActionListCreate.as_view(), name='account-action-list-create'),
    url(r'^account/actions/(?P<pk>[0-9]+)/$',
        views.AccountActionRetrieveUpdate.as_view(), name='account-action-retrieve-update'),
    url(r'^account/actions_by_key/(?P<key>[0-9]+)/$',
        views.AccountActionRetrieveByKey.as_view(), name='account-action-retrieve-by-key'),
    url(r'^account/action_strength/(?P<pk>[0-9]+)/$',
        views.AccountActionStrength.as_view(), name='account-action-strength'),

    url(r'^account/submissions/$', views.AccountSubmissionListCreate.as_view(), name='account-submission-list-create'),
    url(r'^account/submissions/(?P<pk>[0-9]+)/$',
        views.AccountSubmissionRetrieveUpdate.as_view(), name='account-submission-update'),

    url(r'^account/testimonials/$',
        views.AccountTestimonialListCreate.as_view(), name='account-testimonial-list-create'),
    url(r'^account/testimonials/(?P<pk>[0-9]+)/$',
        views.AccountTestimonialRetrieveUpdate.as_view(), name='account-testimonial-update'),

    url(r'^account/donations/$', views.AccountDonationCreate.as_view(), name='account-donation-create'),
    url(r'^account/donations/(?P<pk>[0-9]+)/$',
        views.AccountDonationRetrieveUpdateDestroy.as_view(), name='account-donation-retrieve-update-destroy'),

    url(r'^account/actions/(?P<pk>[0-9]+)/archive/$',
        views.AccountActionArchive.as_view(), name='account-action-archive'),
    url(r'^account/submissions/(?P<pk>[0-9]+)/archive/$',
        views.AccountSubmissionArchive.as_view(), name='account-submission-archive'),
    url(r'^account/submissions/(?P<pk>[0-9]+)/image/$',
        views.AccountSubmissionImageUpdate.as_view(), name='account-submission-image'),

    url(r'^account/volunteer_opportunities/$',
        views.VolunteerOpportunityListCreate.as_view(), name='account-volunteer-opportunity-list-create'),
    url(r'^account/volunteer_opportunities/(?P<pk>[0-9]+)/$',
        views.VolunteerOpportunityRetrieveUpdate.as_view(), name='account-volunteer-opportunity-retrieve-update'),

    # donor account endpoints
    url(r'^donor_account/token/$', views.DonorToken.as_view(), name='donoraccount-token'),
    url(r'^donor_account/delete_token/$', views.DonorDeleteToken.as_view(), name='donoraccount-delete-token'),
    url(r'^donor_account/set_password/$', views.DonorSetPassword.as_view(), name='donoraccount-set-password'),
    url(r'^donor_account/set_password_with_token/$',
        views.DonorSetPasswordWithToken.as_view(), name='donoraccount-set-password-with-token'),
    url(r'^donor_account/send_set_password_email/$',
        views.DonorSendSetPasswordEmail.as_view(), name='donoraccount-send-set-password-email'),
    url(r'^donor_account/me/$', views.DonorMe.as_view(), name='donoraccount-me'),
    url(r'^donor_account/donors/$', views.DonorDonorCreate.as_view(), name='donoraccount-donor-create'),
    url(r'^donor_account/donor/$', views.DonorRetrieveUpdate.as_view(), name='donoraccount-donor-retrieve-update'),
    url(r'^donor_account/profile_strength/$',
        views.DonorProfileStrength.as_view(), name='donoraccount-profile-strength'),
    url(r'^donor_account/donations/$', views.DonorDonationListCreate.as_view(), name='donoraccount-donation-create'),
    url(r'^donor_account/donations/(?P<pk>[0-9]+)/$',
        views.DonorDonationRetrieveUpdateDestroy.as_view(), name='donoraccount-donation-retrieve-update-destroy'),

    # other protected endpoints
    url(r'^files/upload_url/$', views.GetPresignedUploadUrl.as_view(), name='files-upload-url'),
]
