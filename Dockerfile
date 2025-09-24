FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY fhir_portal/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY fhir_portal/ /app/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
