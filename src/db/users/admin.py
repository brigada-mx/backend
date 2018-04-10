from django.contrib import admin

from db.users.models import StaffUser, OrganizationUser, DonorUser


class StaffUserAdmin(admin.ModelAdmin):
    exclude = ('password',)
    readonly_fields = ('password',)


class OrganizationUserAdmin(admin.ModelAdmin):
    exclude = ('set_password_token', 'password', 'is_active', 'last_login', 'set_password_token_created')
    readonly_fields = ('set_password_token', 'password')


class DonorUserAdmin(admin.ModelAdmin):
    exclude = ('set_password_token', 'password', 'last_login', 'set_password_token_created')
    readonly_fields = ('set_password_token', 'password')


admin.site.register(StaffUser, StaffUserAdmin)
admin.site.register(OrganizationUser, OrganizationUserAdmin)
admin.site.register(DonorUser, DonorUserAdmin)
