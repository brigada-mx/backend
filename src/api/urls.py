from django.conf.urls import url
from django.views.decorators.cache import cache_page

from api import views


# `cache_page` also sets `Cache-Control: max-age=<seconds>` in response headers
urlpatterns = [
    # internal endpoints
    url(r'^internal/app_versions/$', views.InternalAppVersionListCreate.as_view()),
    url(r'^internal/organization_users/$', views.InternalOrganizationUserList.as_view()),
    url(r'^internal/debug/throw_exception/$', views.InternalDebugThrowException.as_view()),
    url(r'^internal/email_notifications/$', views.InternalEmailNotificationListCreate.as_view()),

    # public endpoints
    url(r'^$', views.api_root),

    url(r'^actions_cached/$', cache_page(60 * 60)(views.ActionList.as_view())),
    url(r'^volunteer_opportunities_cached/$', cache_page(60 * 60)(views.VolunteerOpportunityList.as_view())),
    url(r'^localities_with_actions/$', cache_page(60 * 60)(views.LocalityWithActionList.as_view())),
    url(r'^landing_metrics/$', cache_page(60 * 60)(views.LandingMetrics.as_view())),
    url(r'^landing/$', cache_page(60 * 60)(views.Landing.as_view())),

    url(r'^webhooks/kobo_submission/$', views.KoboSubmissionWebhook.as_view()),
    url(r'^webhooks/discourse_event/$', views.DiscourseEventWebhook.as_view()),

    url(r'^states/$', cache_page(60 * 5)(views.StateList.as_view())),
    url(r'^municipalities/$', cache_page(60 * 5)(views.MunicipalityList.as_view())),

    url(r'^localities/$', cache_page(60 * 20)(views.LocalityList.as_view()), name='locality-list'),
    url(r'^localities_search/$', views.LocalitySearch.as_view()),
    url(r'^localities/(?P<pk>[0-9]+)/$', views.LocalityDetail.as_view()),

    url(r'^actions/$', views.ActionList.as_view(), name='action-list'),
    url(r'^actions_mini/$', cache_page(60 * 3)(views.ActionMiniList.as_view())),
    url(r'^actions/(?P<pk>[0-9]+)/$', cache_page(60 * 0.5)(views.ActionDetail.as_view())),
    url(r'^actions/(?P<pk>[0-9]+)/log/$', views.ActionLogList.as_view()),

    url(r'^brigada_users/$', views.VolunteerUserCreate.as_view()),

    url(r'^volunteer_opportunities/$',
        cache_page(60 * 3)(views.VolunteerOpportunityList.as_view())),
    url(r'^volunteer_opportunities/(?P<pk>[0-9]+)/$', views.VolunteerOpportunityDetail.as_view()),
    url(r'^volunteer_applications/$', views.VolunteerUserApplicationCreate.as_view()),

    url(r'^shares/$', views.ShareListCreate.as_view()),
    url(r'^share_set_user/$', views.ShareSetUser.as_view()),
    url(r'^action_share/(?P<pk>[0-9]+)/$',
        cache_page(60 * 0.5)(views.ActionShare.as_view())),

    url(r'^support_ticket_create/$', views.SupportTicketCreate.as_view()),

    url(r'^submissions/$', views.SubmissionList.as_view(), name='submission-list'),
    url(r'^testimonials/(?P<pk>[0-9]+)/$', views.TestimonialDetail.as_view()),

    url(r'^donations/$', cache_page(60 * 0.5)(views.DonationList.as_view()), name='donation-list'),

    url(r'^donors_mini/$', views.DonorMiniList.as_view()),
    url(r'^donors/$', cache_page(60 * 3)(views.DonorList.as_view()), name='donor-list'),
    url(r'^donors/(?P<pk>[0-9]+)/$', cache_page(60 * 0.5)(views.DonorDetail.as_view())),

    url(r'^organizations/$', cache_page(60 * 3)(views.OrganizationList.as_view()), name='organization-list'),
    url(r'^organizations/(?P<pk>[0-9]+)/$', cache_page(60 * 0.5)(views.OrganizationDetail.as_view())),

    url(r'^establishments/$', cache_page(60 * 30)(views.EstablishmentList.as_view())),

    # discourse endpoints
    url(r'^discourse/login/$', views.DiscourseLogin.as_view()),
    url(r'^discourse/authenticated_login/$', views.DiscourseAuthLogin.as_view()),

    # organization account endpoints
    url(r'^account/users/$', views.OrganizationUserListCreate.as_view()),
    url(r'^account/users/(?P<pk>[0-9]+)/$', views.OrganizationUserRetrieveUpdate.as_view()),

    url(r'^account/token/$', views.AccountToken.as_view()),
    url(r'^account/delete_token/$', views.AccountDeleteToken.as_view()),
    url(r'^account/set_password/$', views.AccountSetPassword.as_view()),
    url(r'^account/set_password_with_token/$', views.AccountSetPasswordWithToken.as_view()),
    url(r'^account/send_set_password_email/$', views.AccountSendSetPasswordEmail.as_view()),
    url(r'^account/me/$', views.AccountMe.as_view()),

    url(r'^account/organizations/$', views.AccountOrganizationCreate.as_view()),
    url(r'^account/organization/$', views.AccountOrganizationRetrieveUpdate.as_view()),
    url(r'^account/organization/reset_key/$', views.AccountOrganizationResetKey.as_view()),
    url(r'^account/profile_strength/$', views.AccountProfileStrength.as_view()),

    url(r'^account/actions/$', views.AccountActionListCreate.as_view()),
    url(r'^account/actions/(?P<pk>[0-9]+)/$', views.AccountActionRetrieveUpdate.as_view()),
    url(r'^account/actions_by_key/(?P<key>[0-9]+)/$', views.AccountActionRetrieveByKey.as_view()),
    url(r'^account/action_strength/(?P<pk>[0-9]+)/$', views.AccountActionStrength.as_view()),

    url(r'^account/submissions/$', views.AccountSubmissionListCreate.as_view()),
    url(r'^account/submissions/(?P<pk>[0-9]+)/$', views.AccountSubmissionRetrieveUpdate.as_view()),

    url(r'^account/testimonials/$', views.AccountTestimonialListCreate.as_view()),
    url(r'^account/testimonials/(?P<pk>[0-9]+)/$', views.AccountTestimonialRetrieveUpdate.as_view()),

    url(r'^account/donations/$', views.AccountDonationCreate.as_view()),
    url(r'^account/donations/(?P<pk>[0-9]+)/$', views.AccountDonationRetrieveUpdateDestroy.as_view()),

    url(r'^account/actions/(?P<pk>[0-9]+)/archive/$', views.AccountActionArchive.as_view()),
    url(r'^account/submissions/(?P<pk>[0-9]+)/archive/$', views.AccountSubmissionArchive.as_view()),
    url(r'^account/submissions/(?P<pk>[0-9]+)/image/$', views.AccountSubmissionImageUpdate.as_view()),

    url(r'^account/volunteer_opportunities/$', views.VolunteerOpportunityListCreate.as_view()),
    url(r'^account/volunteer_opportunities/(?P<pk>[0-9]+)/$', views.VolunteerOpportunityRetrieveUpdate.as_view()),

    # donor account endpoints
    url(r'^donor_account/users/$', views.DonorUserListCreate.as_view()),
    url(r'^donor_account/users/(?P<pk>[0-9]+)/$', views.DonorUserRetrieveUpdate.as_view()),

    url(r'^donor_account/token/$', views.DonorToken.as_view()),
    url(r'^donor_account/delete_token/$', views.DonorDeleteToken.as_view()),
    url(r'^donor_account/set_password/$', views.DonorSetPassword.as_view()),
    url(r'^donor_account/set_password_with_token/$', views.DonorSetPasswordWithToken.as_view()),
    url(r'^donor_account/send_set_password_email/$', views.DonorSendSetPasswordEmail.as_view()),
    url(r'^donor_account/me/$', views.DonorMe.as_view()),
    url(r'^donor_account/donors/$', views.DonorDonorCreate.as_view()),
    url(r'^donor_account/donor/$', views.DonorRetrieveUpdate.as_view()),
    url(r'^donor_account/profile_strength/$', views.DonorProfileStrength.as_view()),
    url(r'^donor_account/donations/$', views.DonorDonationListCreate.as_view()),
    url(r'^donor_account/donations/(?P<pk>[0-9]+)/$', views.DonorDonationRetrieveUpdateDestroy.as_view()),

    # other protected endpoints
    url(r'^files/upload_url/$', views.GetPresignedUploadUrl.as_view()),
]
