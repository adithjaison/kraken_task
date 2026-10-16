from django.contrib import admin

from .models import Reading


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = (
        "mpan",
        "meter_serial_number",
        "register_id",
        "reading_date",
        "reading_type",
        "reading_value",
        "source_filename",
    )

    search_fields = ("^mpan", "meter_serial_number")
    list_filter = ("reading_type", "reading_date")
    date_hierarchy = "reading_date"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
