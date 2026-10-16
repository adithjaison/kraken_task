from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ReadingRecord:
    mpan: str
    meter_serial_number: str
    register_id: str
    reading_date: datetime
    reading_type: str
    reading_value: Decimal


def parse_reading(record: dict):

    try:
        return ReadingRecord(
            mpan=record["mpan"].strip(),
            meter_serial_number=record["meter_serial_number"].strip(),
            register_id=record["register_id"].strip(),
            reading_date=datetime.strptime(
                record["reading_date"],
                "%Y-%m-%d %H:%M:%S",
            ),
            reading_type=record["reading_type"].strip(),
            reading_value=Decimal(record["reading_value"].strip()),
        )
    except (KeyError, ValueError, InvalidOperation) as exc:
        raise ValueError(f"Invalid reading record: {exc}") from exc
