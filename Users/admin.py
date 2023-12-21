from django.contrib import admin

from Users.models import Users, Channels, SendMessages


class AdminUser(admin.ModelAdmin):
    list_display = ('id', 'tg_id', 'subscription')


class ChannelsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class SendMessagesAdmin(admin.ModelAdmin):
    pass


admin.site.register(SendMessages, SendMessagesAdmin)
admin.site.register(Users, AdminUser)
admin.site.register(Channels, ChannelsAdmin)
