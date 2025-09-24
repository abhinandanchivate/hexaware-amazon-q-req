from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import ensure_list, generate_identifier, isoformat_now


@api_view(['POST'])
def create_session(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'sessionId': generate_identifier('session', override=payload.get('sessionId')),
        'joinUrls': payload.get(
            'joinUrls',
            {
                'patient': 'https://telemedicine.example.com/join/patient-token',
                'provider': 'https://telemedicine.example.com/join/provider-token',
            },
        ),
        'accessWindow': payload.get(
            'accessWindow',
            {
                'start': isoformat_now(),
                'end': isoformat_now(),
            },
        ),
        'sessionSettings': payload.get(
            'sessionSettings',
            {
                'recordingEnabled': False,
                'chatEnabled': True,
                'screenShareEnabled': True,
            },
        ),
    }
    return Response(template)


@api_view(['POST'])
def record_consent(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'sessionId': payload.get('sessionId', generate_identifier('session')),
        'userId': payload.get('userId', generate_identifier('user')),
        'consentType': payload.get('consentType', 'video_recording'),
        'granted': bool(payload.get('granted', True)),
        'recordedAt': payload.get('timestamp', isoformat_now()),
        'ipAddress': payload.get('ipAddress'),
    }
    return Response(template)


@api_view(['GET'])
def metrics(request, session_id: str):
    query = request.query_params
    response = {
        'sessionId': session_id,
        'qualityMetrics': {
            'averageLatency': float(query.get('averageLatency', 0)),
            'packetLoss': float(query.get('packetLoss', 0)),
            'videoQuality': query.get('videoQuality', 'HD'),
            'audioQuality': query.get('audioQuality', 'excellent'),
        },
        'duration': int(query.get('duration', 0)),
        'participants': ensure_list(
            None,
            [
                {
                    'userId': generate_identifier('user'),
                    'connectionTime': int(query.get('connectionTime', 0)),
                    'disconnections': int(query.get('disconnections', 0)),
                }
            ],
        ),
    }
    return Response(response)


urlpatterns = [
    path('sessions', create_session, name='create-session'),
    path('consent', record_consent, name='consent'),
    path('sessions/<str:session_id>/metrics', metrics, name='metrics'),
]
