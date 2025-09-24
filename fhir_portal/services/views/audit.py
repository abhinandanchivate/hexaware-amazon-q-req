from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def log_event(request):
    return Response({
        'auditId': 'audit-uuid-123',
        'status': 'logged',
        'timestamp': '2023-09-01T12:30:45Z',
        'immutableHash': 'sha256:abc123def456...',
    })


@api_view(['GET'])
def export_logs(request):
    return Response({
        'exportId': 'export-uuid-456',
        'status': 'processing',
        'format': request.query_params.get('format', 'csv'),
        'downloadUrl': '/api/v1/audit/exports/export-uuid-456',
        'estimatedCompletion': '2023-09-01T12:35:45Z',
        'digitalSignature': 'MIIC...',
    })


@api_view(['GET'])
def anomalies(request):
    return Response({
        'period': 'P7D',
        'anomalies': [
            {
                'type': 'unusual_access_pattern',
                'userId': 'user-uuid-123',
                'description': 'Access to 50+ patient records in 1 hour',
                'severity': 'medium',
                'timestamp': '2023-09-01T02:00:00Z',
                'score': 0.75,
            }
        ],
    })


urlpatterns = [
    path('events', log_event, name='events'),
    path('export', export_logs, name='export'),
    path('anomalies', anomalies, name='anomalies'),
]
