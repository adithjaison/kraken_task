from django.db import models


class Reading(models.Model):
    mpan = models.CharField(max_length=13, db_index=True)
    meter_serial_number = models.CharField(max_length=50, db_index=True)
    register_id = models.CharField(max_length=20)
    reading_date = models.DateTimeField(db_index=True)
    reading_type = models.CharField(max_length=10)
    reading_value = models.DecimalField(max_digits=15, decimal_places=3)
    source_filename = models.CharField(max_length=255)

    class Meta:
        ordering = ["-reading_date"]

    def __str__(self):
        return f"{self.mpan} - {self.reading_date} - {self.reading_value}"
