# D0010 Meter Reading Importer

A Django application that parses D0010 electricity meter-reading files, stores reading records in a database, and makes them searchable through Django Admin.

## Features

- Parse pipe-delimited D0010 files.
- Group meter readings by MPAN.
- Extract MPAN, meter serial number, register ID, reading date, reading type, and reading value.
- Import readings using a Django management command.
- Prevent duplicate readings from the same source file using a database uniqueness constraint.
- Search readings by MPAN or meter serial number in Django Admin.
- Store the source filename for traceability.
- Include automated tests for parsing and importing.

## Requirements

- Python 3.10 or later
- Django
- SQLite (configured by default)

## Setup

Clone the repository and navigate to the project directory.

Create and activate a virtual environment:

```bash
python3 -m venv krakenv
source krakenv/bin/activate
```

Install the project's dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

## Import D0010 files

Import a single file:

```bash
python manage.py import_d0010 path/to/readings.uff
```

Import multiple files:

```bash
python manage.py import_d0010 path/to/first.uff path/to/second.uff
```

The command reports how many new readings were imported. Re-importing an identical file should not create duplicate database records.

## Django Admin

Create an administrator account:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/admin/ and sign in.

Readings can be searched by MPAN or meter serial number. The list view displays reading details and the source filename.

## Tests

Run the complete test suite:

```bash
python manage.py test
```

Check the Django configuration:

```bash
python manage.py check
```

## Implementation notes

The application uses Django models and migrations for persistence, a management command for file imports, and Django Admin for support staff to search readings.

The import parser preserves empty fields when splitting pipe-delimited records, because field positions matter in the D0010 format.
