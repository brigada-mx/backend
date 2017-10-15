from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from api import views

urlpatterns = [
    url(r'^$', views.api_root),

    url(r'^invite/$', views.CreateNurseReservationConnection.as_view(), name="invite"),
    url(r'^accept/$', views.AcceptNurseReservationConnection.as_view(), name="accept"),

    url(r'^(?P<user_type>(clients|nurses))/set_password/(?P<code>[-\w]+)/$', views.SetPasswordForm.as_view(), name="set-password-form"),
    url(r'^set_password_success/$', views.SetPasswordSuccess.as_view(), name="set-password-success"),

    url(r'^clients/auth/$', views.ObtainClientAuthToken.as_view(), name="client-auth"),
    url(r'^clients/send_password_email/$', views.ClientSendSetPasswordEmail.as_view(), name="client-send-password-email"),
    url(r'^clients/set_password/$', views.ClientSetPassword.as_view(), name="client-set-password"),
    url(r'^clients/create_account/$', views.ClientCreateUserAccount.as_view(), name="client-create-account"),
    url(r'^clients/create_account_address/$', views.AddressCreateUnauthenticated.as_view(), name="client-create-account-address"),
    url(r'^clients/create_account_patient/$', views.PatientCreateUnauthenticated.as_view(), name="client-create-account-patient"),
    url(r'^clients/$', views.ClientList.as_view(), name="client-list"),
    url(r'^clients/(?P<pk>[0-9]+)/$', views.ClientDetail.as_view(), name="client-detail"),
    url(r'^clients/(?P<pk>[0-9]+)/change_account_holder/$', views.ClientChangeAccountHolder.as_view(), name="client-change-account-holder"),
    url(r'^clients/(?P<pk>[0-9]+)/cards/add/$', views.ClientAddCards.as_view(), name="client-add-cards"),
    url(r'^clients/add_fcm_token/$', views.ClientAddFCMToken.as_view(), name="client-add-fcm-token"),

    url(r'^reservations/$', views.ReservationList.as_view(), name="reservation-list"),
    url(r'^reservations/(?P<pk>[0-9]+)/$', views.ReservationDetail.as_view(), name="reservation-detail"),
    url(r'^activityfeed/$', views.ActivityFeedItemList.as_view(), name="activityfeeditem-list"),

    url(r'^care_circle_members/$', views.CareCircleMemberList.as_view(), name="care-circle-member-list"),
    url(r'^care_circle_members/(?P<pk>[0-9]+)/$', views.CareCircleMemberDetail.as_view(), name="care-circle-member-detail"),
    url(r'^care_circle_notify/$', views.CareCircleNotify.as_view(), name="care-circle-notify"),

    url(r'^nurse_reviews/$', views.NurseReviewList.as_view(), name="nursereview-list"),
    url(r'^nurse_reviews/(?P<pk>[0-9]+)/$', views.NurseReviewDetail.as_view(), name="nursereview-detail"),

    url(r'^nurses/auth/$', views.ObtainNurseAuthToken.as_view(), name="nurse-auth"),
    url(r'^nurses/send_password_email/$', views.NurseSendSetPasswordEmail.as_view(), name="nurse-send-password-email"),
    url(r'^nurses/$', views.NurseList.as_view(), name="nurse-list"),
    url(r'^nurses/create/$', views.NurseUserCreate.as_view(), name="nurse-create"),
    url(r'^nurses/(?P<pk>[0-9]+)/$', views.NurseDetail.as_view(), name="nurse-detail"),
    url(r'^nurses/care_schedule_tasks/$', views.NurseCareScheduleTaskList.as_view(),
        name="nursecarescheduletask-list"),
    url(r'^nurses/care_schedule_tasks/(?P<pk>[0-9]+)/$', views.NurseCareScheduleTaskDetail.as_view(),
        name="nursecarescheduletask-detail"),
    url(r'^nurses/add_fcm_token/$', views.NurseAddFCMToken.as_view(), name="nurse-add-fcm-token"),

    url(r'^shifts/$', views.ShiftList.as_view(), name="shift-list"),
    url(r'^shifts-unprotected/$', views.ShiftUnprotectedList.as_view(), name="shift-unprotected-list"),
    url(r'^shifts/(?P<pk>[0-9]+)/$', views.ShiftDetail.as_view(), name='shift-detail'),

    url(r'^shifts/(?P<pk>[0-9]+)/cancel/$', views.ShiftCancel.as_view(), name='shift-cancel'),
    url(r'^shifts/(?P<pk>[0-9]+)/checkin/$', views.ShiftCheckin.as_view(), name='shift-checkin'),
    url(r'^shifts/(?P<pk>[0-9]+)/checkout/$', views.ShiftCheckout.as_view(), name='shift-checkout'),
    url(r'^shifts/(?P<pk>[0-9]+)/signature/$', views.ShiftSignatureUpload.as_view(), name='shift-signature'),
    url(r'^shifts/(?P<pk>[0-9]+)/request-signature/$', views.ShiftRequestSignature.as_view(), name='shift-request-signature'),

    url(r'^shifts/(?P<pk>[0-9]+)/incidents/$', views.ShiftIncidentCreate.as_view(), name='shiftincident'),
    url(r'^shifts/incidents/\?shift_id=(?P<pk>[0-9]+)', views.ShiftIncidentList.as_view(), name='shiftincident-list-shift'),
    url(r'^shifts/incidents/$', views.ShiftIncidentList.as_view(), name='shiftincident-list'),
    url(r'^shifts/incidents/(?P<pk>[0-9]+)/$', views.ShiftIncidentDetail.as_view(), name='shiftincident-detail'),

    url(r'^shift_schedules/$', views.ShiftScheduleList.as_view(), name='shiftschedule-list'),
    url(r'^shift_schedules/(?P<pk>[0-9]+)/$', views.ShiftScheduleDetail.as_view(), name='shiftschedule-detail'),
    url(r'^shift_schedule_days/$', views.ShiftScheduleDayList.as_view(), name='shiftscheduleday-list'),
    url(r'^shift_schedule_posting_responses/$', views.ShiftSchedulePostingResponseList.as_view(), name='shiftschedulepostingresponse-list'),
    url(r'^shift_schedule_postings/(?P<pk>[0-9]+)/respond/$', views.ShiftSchedulePostingRespond.as_view(), name='shiftscheduleposting-respond'),

    url(r'^care_schedules/$', views.CareScheduleList.as_view(), name='careschedule-list'),
    url(r'^care_schedules/(?P<pk>[0-9]+)/$', views.CareScheduleDetail.as_view(), name='careschedule-detail'),

    url(r'^care_log_entries/report/$', views.CareLogEntryReport.as_view(), name='carelogentry-report'),
    url(r'^care_log_entries/send_report/$', views.CareLogEntrySendReport.as_view(), name='carelogentry-send-report'),
    url(r'^care_log_entries/send_report/care_circle/$', views.CareLogEntrySendReportToCareCircle.as_view(), name='carelogentry-send-report-carecircle'),
    url(r'^care_log_entries/\?shift_id=(?P<pk>[0-9]+)', views.CareLogEntryList.as_view(), name='carelogentry-list-shift'),
    url(r'^care_log_entries/$', views.CareLogEntryList.as_view(), name='carelogentry-list'),
    url(r'^care_log_entries/(?P<pk>[0-9]+)/$', views.CareLogEntryDetail.as_view(), name='carelogentry-detail'),

    url(r'^patients/$', views.PatientList.as_view(), name='patient-list'),
    url(r'^patients/(?P<pk>[0-9]+)/$', views.PatientDetail.as_view(), name='patient-detail'),

    url(r'^addresses/$', views.AddressList.as_view(), name='address-list'),
    url(r'^addresses/(?P<pk>[0-9]+)/$', views.AddressDetail.as_view(), name='address-detail'),

    url(r'^notifications/fcm/$', views.FCMNotificationList.as_view(), name='notification-list-fcm'),

    url(r'^rankings/nurse_shift/$', views.NurseShiftRankings.as_view(), name='nurse-shift-rankings'),

    url(r'^metrics/care_log_entries/$', views.CareLogEntryMetrics.as_view(), name='metrics-carelogentry'),
    url(r'^metrics/shifts/$', views.ShiftMetrics.as_view(), name='metrics-shifts'),
    url(r'^metrics/posting_responses/$', views.PostingResponseMetrics.as_view(), name='metrics-posting-responses'),
    url(r'^metrics/nurses/$', views.NurseMetrics.as_view(), name='metrics-nurses'),
    url(r'^metrics/nurse_reviews/$', views.NurseReviewMetrics.as_view(), name='metrics-nurse-reviews'),
    url(r'^metrics/clients/$', views.ClientMetrics.as_view(), name='metrics-clients'),
]

# allow API to parse and return many different formats, not just default JSON
urlpatterns = format_suffix_patterns(urlpatterns)
