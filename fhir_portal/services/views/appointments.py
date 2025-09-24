from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import AppointmentRecord, WaitlistEntry
from ..sample_utils import (
    deep_merge,
    ensure_list,
    generate_identifier,
    isoformat_now,
    parse_iso_date,
    parse_iso_datetime,
)


def _participant_reference(participants: list[dict], resource_type: str) -> str:
    for participant in participants:
        actor = participant.get('actor') if isinstance(participant, dict) else None
        reference = actor.get('reference') if isinstance(actor, dict) else None
        if reference and reference.startswith(f'{resource_type}/'):
            return reference
    return ''


def _appointment_template(payload: dict | None = None) -> dict:
    payload = payload or {}
    return {
        'resourceType': 'Appointment',
        'id': generate_identifier('appt', override=payload.get('id')),
        'meta': {
            'versionId': payload.get('meta', {}).get('versionId', '1'),
            'lastUpdated': isoformat_now(),
        },
        'status': payload.get('status', 'booked'),
        'start': payload.get('start', isoformat_now()),
        'end': payload.get('end', isoformat_now()),
        'confirmationCode': payload.get('confirmationCode', generate_identifier('conf')),
        'participant': ensure_list(payload.get('participant'), []),
    }


@api_view(['POST'])
def book(request):
    payload = request.data if isinstance(request.data, dict) else {}
    merged = deep_merge(_appointment_template(payload), payload)
    participants = ensure_list(merged.get('participant'), [])
    record, created = AppointmentRecord.objects.update_or_create(
        appointment_id=merged['id'],
        defaults={
            'status': merged.get('status', 'booked'),
            'start': parse_iso_datetime(merged.get('start')),
            'end': parse_iso_datetime(merged.get('end')),
            'patient_reference': _participant_reference(participants, 'Patient'),
            'practitioner_reference': _participant_reference(participants, 'Practitioner'),
            'service_category': ensure_list(merged.get('serviceCategory'), [{}])[0]
            .get('coding', [{}])[0]
            .get('code', ''),
            'appointment_type': ensure_list(merged.get('appointmentType', {}).get('coding'), [{}])[0]
            .get('code', ''),
            'data': merged,
        },
    )
    merged['id'] = record.appointment_id
    return Response(
        merged,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(['GET'])
def availability(request):
    query = request.query_params
    practitioner = query.get('practitioner')
    records = AppointmentRecord.objects.all()
    if practitioner:
        records = records.filter(practitioner_reference__icontains=practitioner)

    date_query = query.get('date')
    if date_query:
        parsed_date = parse_iso_date(date_query)
        if parsed_date:
            records = records.filter(start__date=parsed_date)

    slots = [
        {
            'start': record.start.isoformat() if record.start else isoformat_now(),
            'end': record.end.isoformat() if record.end else isoformat_now(),
            'type': record.status,
        }
        for record in records
    ]

    if not slots:
        slots = ensure_list(
            None,
            [
                {
                    'start': isoformat_now(),
                    'end': isoformat_now(),
                    'type': 'available',
                }
            ],
        )

    return Response(
        {
            'date': date_query or isoformat_now().split('T')[0],
            'practitioner': practitioner or generate_identifier('practitioner'),
            'availableSlots': slots,
        }
    )


@api_view(['POST'])
def waitlist(request, appointment_id: str):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'appointmentId': appointment_id,
        'status': payload.get('status', 'added'),
        'priority': payload.get('priority', 'routine'),
        'notificationPreferences': payload.get(
            'notificationPreferences',
            {'email': True, 'sms': True, 'advanceNotice': '24h'},
        ),
    }
    WaitlistEntry.objects.update_or_create(
        appointment_id=appointment_id,
        patient_id=payload.get('patientId', generate_identifier('patient')),
        defaults={
            'preferred_dates': ensure_list(payload.get('preferredDates'), []),
            'preferred_times': ensure_list(payload.get('preferredTimes'), []),
            'priority': template['priority'],
            'notification_preferences': template['notificationPreferences'],
        },
    )
    return Response(template)


urlpatterns = [
    path('', book, name='book'),
    path('availability', availability, name='availability'),
    path('<str:appointment_id>/waitlist', waitlist, name='waitlist'),
]
