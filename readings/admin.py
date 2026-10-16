from django.contrib import admin

from readings.models import Reading


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = (
        "mpan",
        "meter_serial_number",
        "register_id",
        "reading_date",
        "reading_value",
        "source_filename",
    )

    search_fields = (
        "mpan",
        "meter_serial_number",
    )

    list_filter = (
        "reading_type",
        "reading_date",
    )

    ordering = ("-reading_date",)
