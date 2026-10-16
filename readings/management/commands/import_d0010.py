import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from readings.models import Reading
from readings.services.parser import parse_d0010

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import D0010 meter readings from one or more files."

    def add_arguments(self, parser):
        parser.add_argument(
            "files",
            nargs="+",
            type=Path,
            help="Path to one or more D0010 files.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate files and report import counts without saving readings.",
        )

    def handle(self, *args, **options):
        file_paths = options["files"]
        dry_run = options["dry_run"]

        # Step 1: Check that all requested files exist.
        missing = [path for path in file_paths if not path.is_file()]

        if missing:
            message = "File not found: " + ", ".join(map(str, missing))
            logger.error(message)
            raise CommandError(message)

        # Step 2: Parse every file before making any database changes.
        parsed_files = []

        for path in file_paths:
            try:
                parsed_file = parse_d0010(path)
                parsed_files.append((path, parsed_file))

            except (ValueError, OSError) as exc:
                logger.exception("Could not parse D0010 file %s", path)
                raise CommandError(f"Could not import {path}: {exc}") from exc

        total_inserted = 0
        total_duplicates = 0

        try:
            # Step 3: Keep the database changes for the entire batch atomic.
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

                    # The identity used for duplicate detection matches the
                    # existing model's unique constraint, scoped by filename.
                    existing_keys = set(
                        Reading.objects.filter(source_filename=path.name).values_list(
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

                    inserted_count = len(new_readings)

                    if dry_run:
                        # Do not write anything to the database.
                        self.stdout.write(
                            f"{path.name}: would import "
                            f"{inserted_count} new readings; "
                            f"would skip {skipped_duplicates} duplicates."
                        )
                    else:
                        Reading.objects.bulk_create(new_readings)

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"{path.name}: imported "
                                f"{inserted_count} new readings; "
                                f"skipped {skipped_duplicates} duplicates."
                            )
                        )

                    total_inserted += inserted_count
                    total_duplicates += skipped_duplicates

        except (IntegrityError, OSError) as exc:
            logger.exception("D0010 import batch failed")
            raise CommandError(
                f"Import failed; no files in this batch were committed: {exc}"
            ) from exc

        # Step 4: Report the overall result.
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run complete. Would import {total_inserted} new "
                    f"readings; would skip {total_duplicates} duplicates "
                    f"across {len(parsed_files)} file(s). "
                    "No readings were saved."
                )
            )
            logger.info(
                "D0010 dry run completed for %d file(s): "
                "%d new readings, %d duplicates",
                len(parsed_files),
                total_inserted,
                total_duplicates,
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Import complete. Imported {total_inserted} new "
                    f"readings; skipped {total_duplicates} duplicates "
                    f"across {len(parsed_files)} file(s)."
                )
            )
            logger.info(
                "D0010 import completed for %d file(s): "
                "%d new readings, %d duplicates",
                len(parsed_files),
                total_inserted,
                total_duplicates,
            )
