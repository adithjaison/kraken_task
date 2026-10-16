from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from readings.models import Reading
from readings.services.parser import parse_d0010


class Command(BaseCommand):
    help = "Import D0010 meter readings from one or more files."

    def add_arguments(self, parser):
        parser.add_argument(
            "files",
            nargs="+",
            type=Path,
            help="Path to one or more D0010 files.",
        )

    def handle(self, *args, **options):
        total_imported = 0

        for file_path in options["files"]:
            if not file_path.is_file():
                raise CommandError(f"File not found: {file_path}")

            try:
                parsed_file = parse_d0010(file_path)

                readings = [
                    Reading(
                        mpan=reading.mpan,
                        meter_serial_number=reading.meter_serial_number,
                        register_id=reading.register_id,
                        reading_date=reading.reading_date,
                        reading_type=reading.reading_type,
                        reading_value=reading.reading_value,
                        source_filename=file_path.name,
                    )
                    for group in parsed_file.mpan_groups
                    for reading in group.readings
                ]

                with transaction.atomic():
                    Reading.objects.bulk_create(readings)

            except (ValueError, OSError) as exc:
                raise CommandError(f"Could not import {file_path}: {exc}") from exc

            count = len(readings)
            total_imported += count

            self.stdout.write(
                self.style.SUCCESS(f"Imported {count} readings from {file_path.name}")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Total readings imported: {total_imported}"
            )
        )
