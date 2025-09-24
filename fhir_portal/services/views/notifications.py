from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import ensure_list, generate_identifier, isoformat_now


@api_view(['POST'])
def send_notification(request):
    payload = request.data if isinstance(request.data, dict) else {}
    channels = ensure_list(
        payload.get('channels'),
        [
            {
                'type': 'email',
                'status': 'queued',
                'estimatedDelivery': isoformat_now(),
            }
        ],
    )
    template = {
        'notificationId': generate_identifier('notif', override=payload.get('notificationId')),
        'status': payload.get('status', 'scheduled'),
        'channels': channels,
        'scheduledAt': payload.get('scheduledAt', isoformat_now()),
    }
    return Response(template)


@api_view(['POST'])
def create_template(request):
    payload = request.data if isinstance(request.data, dict) else {}
    return Response(
        {
            'templateId': generate_identifier('template', override=payload.get('templateId')),
            'name': payload.get('name', 'appointment_reminder'),
            'channels': payload.get('channels', {}),
            'variables': ensure_list(payload.get('variables'), ['patientName']),
        }
    )


@api_view(['POST'])
def bulk(request):
    payload = request.data if isinstance(request.data, dict) else {}
    recipients = ensure_list(payload.get('recipients'), [])
    return Response(
        {
            'campaignName': payload.get('campaignName', 'campaign'),
            'status': payload.get('status', 'scheduled'),
            'scheduledAt': payload.get('scheduledAt', isoformat_now()),
            'recipientCount': len(recipients),
        }
    )


urlpatterns = [
    path('send', send_notification, name='send'),
    path('templates', create_template, name='templates'),
    path('bulk', bulk, name='bulk'),
]
