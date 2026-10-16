from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

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
        file_paths = options["files"]

        # Validate every file before parsing or importing anything.
        missing = [path for path in file_paths if not path.is_file()]
        if missing:
            raise CommandError(
                "File not found: " + ", ".join(str(path) for path in missing)
            )

        # Parse every file before making database changes.
        parsed_files = []

        for path in file_paths:
            try:
                parsed_files.append((path, parse_d0010(path)))
            except (ValueError, OSError) as exc:
                raise CommandError(f"Could not import {path}: {exc}") from exc

        total_inserted = 0
        total_duplicates = 0

        try:
            # All files are committed together or rolled back together.
            with transaction.atomic():
                for path, parsed_file in parsed_files:
                    readings = [
                        Reading(
                            mpan=reading.mpan,
                            meter_serial_number=reading.meter_serial_number,
                            register_id=reading.register_id,
                            reading_date=reading.reading_date,
                            reading_type=reading.reading_type,
                            reading_value=reading.reading_value,
                            source_filename=path.name,
                        )
                        for group in parsed_file.mpan_groups
                        for reading in group.readings
                    ]

                    # Match the fields in the database uniqueness constraint.
                    existing_keys = set(
                        Reading.objects.filter(
                            source_filename=path.name,
                        ).values_list(
                            "mpan",
                            "meter_serial_number",
                            "register_id",
                            "reading_date",
                            "reading_type",
                            "reading_value",
                        )
                    )

                    new_readings = []
                    seen_keys = set(existing_keys)
                    skipped_duplicates = 0

                    for reading in readings:
                        key = (
                            reading.mpan,
                            reading.meter_serial_number,
                            reading.register_id,
                            reading.reading_date,
                            reading.reading_type,
                            reading.reading_value,
                        )

                        if key in seen_keys:
                            skipped_duplicates += 1
                            continue

                        new_readings.append(reading)
                        seen_keys.add(key)

                    # Insert only readings not already present or repeated
                    # within this file. The database constraint remains
                    # the final protection against duplicate records.
                    Reading.objects.bulk_create(new_readings)

                    inserted_count = len(new_readings)
                    total_inserted += inserted_count
                    total_duplicates += skipped_duplicates

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{path.name}: imported {inserted_count} new "
                            f"readings; skipped {skipped_duplicates} duplicates."
                        )
                    )

        except (IntegrityError, OSError) as exc:
            raise CommandError(
                f"Import failed; no files in this batch were committed: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Imported {total_inserted} new readings; "
                f"skipped {total_duplicates} duplicates across "
                f"{len(parsed_files)} file(s)."
            )
        )
