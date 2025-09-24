from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def send_notification(request):
    return Response({
        'notificationId': 'notif-uuid-123',
        'status': 'scheduled',
        'channels': [
            {
                'type': 'email',
                'status': 'queued',
                'estimatedDelivery': '2023-09-14T20:00:30Z',
            },
            {
                'type': 'sms',
                'status': 'queued',
                'estimatedDelivery': '2023-09-14T20:00:15Z',
            },
        ],
    })


@api_view(['POST'])
def create_template(request):
    return Response({
        'templateId': 'template-uuid-123',
        'name': request.data.get('name', 'appointment_reminder'),
        'channels': request.data.get('channels', {}),
        'variables': request.data.get('variables', []),
    })


@api_view(['POST'])
def bulk(request):
    return Response({
        'campaignName': request.data.get('campaignName', 'campaign'),
        'status': 'scheduled',
        'scheduledAt': request.data.get('scheduledAt', '2023-09-20T10:00:00Z'),
        'recipientCount': len(request.data.get('recipients', [])),
    })


urlpatterns = [
    path('send', send_notification, name='send'),
    path('templates', create_template, name='templates'),
    path('bulk', bulk, name='bulk'),
]
