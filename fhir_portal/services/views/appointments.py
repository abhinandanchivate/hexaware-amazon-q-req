from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import deep_merge, ensure_list, generate_identifier, isoformat_now


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
    return Response(deep_merge(_appointment_template(payload), payload))


@api_view(['GET'])
def availability(request):
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
            'date': request.query_params.get('date', isoformat_now().split('T')[0]),
            'practitioner': request.query_params.get(
                'practitioner', generate_identifier('practitioner')
            ),
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
    return Response(template)


urlpatterns = [
    path('', book, name='book'),
    path('availability', availability, name='availability'),
    path('<str:appointment_id>/waitlist', waitlist, name='waitlist'),
]
