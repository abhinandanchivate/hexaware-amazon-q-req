from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def create_session(request):
    return Response({
        'sessionId': 'session-uuid-101',
        'joinUrls': {
            'patient': 'https://telemedicine.example.com/join/patient-token-123',
            'provider': 'https://telemedicine.example.com/join/provider-token-456',
        },
        'accessWindow': {
            'start': '2023-09-15T08:50:00Z',
            'end': '2023-09-15T09:40:00Z',
        },
        'sessionSettings': {
            'recordingEnabled': False,
            'chatEnabled': True,
            'screenShareEnabled': True,
        },
    })


@api_view(['POST'])
def record_consent(request):
    return Response({
        'sessionId': request.data.get('sessionId', 'session-uuid-101'),
        'userId': request.data.get('userId', 'patient-uuid-123'),
        'consentType': request.data.get('consentType', 'video_recording'),
        'granted': request.data.get('granted', True),
        'recordedAt': request.data.get('timestamp', '2023-09-15T08:55:00Z'),
    })


@api_view(['GET'])
def metrics(request, session_id: str):
    return Response({
        'sessionId': session_id,
        'qualityMetrics': {
            'averageLatency': 45,
            'packetLoss': 0.2,
            'videoQuality': 'HD',
            'audioQuality': 'excellent',
        },
        'duration': 1800,
        'participants': [
            {
                'userId': 'patient-uuid-123',
                'connectionTime': 1795,
                'disconnections': 0,
            }
        ],
    })


urlpatterns = [
    path('sessions', create_session, name='create-session'),
    path('consent', record_consent, name='consent'),
    path('sessions/<str:session_id>/metrics', metrics, name='metrics'),
]
