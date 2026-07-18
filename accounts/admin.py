from django.contrib import admin

from .models import LoginRecord, Profile, WatchSession

# Register your models here.
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "location",
        "date_created",
        "date_updated",
    )

    search_fields = (
        "user__username",
        "user__email",
        "location",
    )


@admin.register(LoginRecord)
class LoginRecordAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "login_time",
        "ip_address",
    )

    search_fields = (
        "user__username",
        "ip_address",
    )

    list_filter = (
        "login_time",
    )


@admin.register(WatchSession)
class WatchSessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "movie",
        "seconds_watched",
        "completed",
        "last_watched_at",
    )

    search_fields = (
        "user__username",
        "movie__title",
    )

    list_filter = (
        "completed",
        "last_watched_at",
    )