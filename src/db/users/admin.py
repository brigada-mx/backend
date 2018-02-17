from django.contrib import admin

from db.users.models import StaffUser, OrganizationUser


class StaffUserAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['password'].initial = '_'
        return form


class OrganizationUserAdmin(admin.ModelAdmin):
    exclude = ('set_password_token', 'password')
    readonly_fields = ('set_password_token', 'password')


admin.site.register(StaffUser, StaffUserAdmin)
admin.site.register(OrganizationUser, OrganizationUserAdmin)
