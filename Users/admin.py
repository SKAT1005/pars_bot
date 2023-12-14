from django.contrib import admin

from Users.models import Users, Channels


class AdminUser(admin.ModelAdmin):
    list_display = ('id', 'tg_id', 'subscription')


class ChannelsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


admin.site.register(Users, AdminUser)
admin.site.register(Channels, ChannelsAdmin)
