from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from readings.models import Reading


class ImportD0010CommandTests(TestCase):
    def setUp(self):
        self.sample_file = Path(__file__).parent / "sample_data" / "sample_d0010.uff"

    def test_imports_readings_into_database(self):
        call_command("import_d0010", str(self.sample_file))

        self.assertEqual(Reading.objects.count(), 13)

    def test_imported_reading_has_expected_fields(self):
        call_command("import_d0010", str(self.sample_file))

        reading = Reading.objects.get(
            mpan="1200023305967",
            meter_serial_number="F75A 00802",
        )

        self.assertEqual(reading.register_id, "S")
        self.assertEqual(
            timezone.localtime(reading.reading_date).strftime("%Y-%m-%dT%H:%M:%S"),
            "2016-02-22T00:00:00",
        )
        self.assertEqual(str(reading.reading_value), "56311.000")
        self.assertEqual(
            reading.source_filename,
            "sample_d0010.uff",
        )

    def test_missing_file_raises_command_error(self):
        missing_file = self.sample_file.parent / "missing.uff"

        with self.assertRaises(CommandError):
            call_command("import_d0010", str(missing_file))
