from django.contrib import admin

from db.users.models import StaffUser, OrganizationUser


class StaffUserAdmin(admin.ModelAdmin):
    exclude = ('password',)
    readonly_fields = ('password',)


class OrganizationUserAdmin(admin.ModelAdmin):
    exclude = ('set_password_token', 'password')
    readonly_fields = ('set_password_token', 'password')


admin.site.register(StaffUser, StaffUserAdmin)
admin.site.register(OrganizationUser, OrganizationUserAdmin)
