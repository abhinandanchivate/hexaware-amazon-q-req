# FHIR Patient Portal (Django)

This Django project provides stubbed endpoints that mirror the "FHIR Patient Portal - Complete API Specifications". Each endpoint returns sample payloads from the specification so that frontend or integration teams can prototype against realistic responses while the business logic is still under development.

## Project Layout

```
fhir_portal/
  manage.py
  fhir_portal/
    settings.py
    urls.py
  services/
    urls.py
    fhir_urls.py
    views/
      *.py
```

* `services/urls.py` mounts each domain-specific router under `/api/v1/`.
* `services/fhir_urls.py` provides the `/fhir/R4` gateway routes.
* `services/views/` contains dedicated modules for HL7 parsing, patient management, observations, appointments, authentication, roles, telemedicine, notifications, analytics, and audit logging.

## Running Locally

### Prerequisites

* Python 3.11+
* MySQL 8.0+

Create a database and user for the portal:

```sql
CREATE DATABASE fhir_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fhir_user'@'%' IDENTIFIED BY 'fhir_password';
GRANT ALL PRIVILEGES ON fhir_portal.* TO 'fhir_user'@'%';
FLUSH PRIVILEGES;
```

### Environment configuration

The Django settings read the connection parameters from the following environment variables, defaulting to the values shown above:

* `MYSQL_DATABASE`
* `MYSQL_USER`
* `MYSQL_PASSWORD`
* `MYSQL_HOST`
* `MYSQL_PORT`

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MYSQL_HOST=127.0.0.1  # adjust as needed
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

The project intentionally uses static sample responses to document the contract. Replace the response bodies with production logic as services mature.
