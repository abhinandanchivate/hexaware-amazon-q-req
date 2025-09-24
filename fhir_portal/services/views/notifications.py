from django.urls import path
from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import NotificationCampaign, NotificationMessage, NotificationTemplate
from ..sample_utils import (
    ensure_list,
    generate_identifier,
    isoformat_now,
    parse_iso_datetime,
)


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
    NotificationMessage.objects.update_or_create(
        notification_id=template['notificationId'],
        defaults={
            'recipient_id': payload.get('recipientId', ''),
            'template': payload.get('template', ''),
            'channels': channels,
            'data': payload.get('data', {}),
            'status': template['status'],
            'scheduled_at': parse_iso_datetime(template['scheduledAt']),
        },
    )
    return Response(template, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def create_template(request):
    payload = request.data if isinstance(request.data, dict) else {}
    response = {
        'templateId': generate_identifier('template', override=payload.get('templateId')),
        'name': payload.get('name', 'appointment_reminder'),
        'channels': payload.get('channels', {}),
        'variables': ensure_list(payload.get('variables'), ['patientName']),
    }
    NotificationTemplate.objects.update_or_create(
        name=response['name'],
        defaults={
            'channels': response['channels'],
            'variables': response['variables'],
        },
    )
    return Response(response, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def bulk(request):
    payload = request.data if isinstance(request.data, dict) else {}
    recipients = ensure_list(payload.get('recipients'), [])
    response = {
        'campaignName': payload.get('campaignName', 'campaign'),
        'status': payload.get('status', 'scheduled'),
        'scheduledAt': payload.get('scheduledAt', isoformat_now()),
        'recipientCount': len(recipients),
    }
    NotificationCampaign.objects.update_or_create(
        campaign_name=response['campaignName'],
        defaults={
            'template_name': payload.get('template', ''),
            'channels': ensure_list(payload.get('channels'), []),
            'recipients': recipients,
            'scheduled_at': parse_iso_datetime(response['scheduledAt']),
        },
    )
    return Response(response)


urlpatterns = [
    path('send', send_notification, name='send'),
    path('templates', create_template, name='templates'),
    path('bulk', bulk, name='bulk'),
]
