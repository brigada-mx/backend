from django.views.generic import FormView, TemplateView
from django.http import Http404

from rest_framework.reverse import reverse

from webapp.users.forms import UserSetPasswordForm
from database.clients.models import ClientUser
from database.nurses.models import NurseUser


class SetPasswordForm(FormView):
    """Render form for resetting user password, identifying user with `code`
    embedded in URL. This is not an `APIView`.
    """
    template_name = 'users/set_password.html'
    form_class = UserSetPasswordForm

    def get_success_url(self):
        return reverse('api:set-password-success')

    def dispatch(self, request, user_type, *args, **kwargs):
        code = kwargs.get('code', None)
        if user_type == 'clients':
            self.user = ClientUser.objects.filter(set_password_code=code).first()
        if user_type == 'nurses':
            self.user = NurseUser.objects.filter(set_password_code=code).first()

        if not code or not self.user: # blank codes aren't valid
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        self.user.set_password(form.cleaned_data['password'])
        self.user.set_password_code = ''
        self.user.save()
        return super(SetPasswordForm, self).form_valid(form)


class SetPasswordSuccess(TemplateView):
    template_name = 'users/password_success.html'
