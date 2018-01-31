from django.contrib import admin

from db.users.models import StaffUser


class UserAdmin(admin.ModelAdmin):
    exclude = ('password',)
    readonly_fields = ('password',)


admin.site.register(StaffUser, UserAdmin)
