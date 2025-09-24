from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def book(request):
    return Response({
        'resourceType': 'Appointment',
        'id': 'appt-uuid-789',
        'meta': {
            'versionId': '1',
            'lastUpdated': '2023-09-01T12:30:45Z',
        },
        'status': 'booked',
        'start': '2023-09-15T09:00:00Z',
        'end': '2023-09-15T09:30:00Z',
        'confirmationCode': 'CONF123456',
    })


@api_view(['GET'])
def availability(request):
    return Response({
        'date': request.query_params.get('date', '2023-09-15'),
        'practitioner': request.query_params.get('practitioner', 'doc-uuid-456'),
        'availableSlots': [
            {
                'start': '2023-09-15T09:00:00Z',
                'end': '2023-09-15T09:30:00Z',
                'type': 'available',
            },
            {
                'start': '2023-09-15T10:00:00Z',
                'end': '2023-09-15T10:30:00Z',
                'type': 'tentative',
            },
        ],
    })


@api_view(['POST'])
def waitlist(request, appointment_id: str):
    return Response({
        'appointmentId': appointment_id,
        'status': 'added',
        'priority': request.data.get('priority', 'routine'),
        'notificationPreferences': request.data.get(
            'notificationPreferences',
            {'email': True, 'sms': True, 'advanceNotice': '24h'},
        ),
    })


urlpatterns = [
    path('', book, name='book'),
    path('availability', availability, name='availability'),
    path('<str:appointment_id>/waitlist', waitlist, name='waitlist'),
]
