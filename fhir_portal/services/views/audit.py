from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import AuditAnomalyRecord, AuditEventRecord, AuditExportRecord
from ..sample_utils import ensure_list, generate_identifier, isoformat_now, parse_iso_datetime


@api_view(['POST'])
def log_event(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'auditId': generate_identifier('audit', override=payload.get('auditId')),
        'status': payload.get('status', 'logged'),
        'timestamp': payload.get('timestamp', isoformat_now()),
        'immutableHash': payload.get('immutableHash', 'sha256:placeholder'),
    }
    AuditEventRecord.objects.update_or_create(
        audit_id=template['auditId'],
        defaults={
            'event_type': payload.get('eventType', ''),
            'user_id': payload.get('userId', ''),
            'resource_type': payload.get('resourceType', ''),
            'resource_id': payload.get('resourceId', ''),
            'action': payload.get('action', ''),
            'timestamp_value': parse_iso_datetime(template['timestamp']),
            'metadata': payload.get('metadata', {}),
        },
    )
    return Response(template)


@api_view(['GET'])
def export_logs(request):
    response = {
        'exportId': request.query_params.get('exportId', generate_identifier('export')),
        'status': request.query_params.get('status', 'processing'),
        'format': request.query_params.get('format', 'csv'),
        'downloadUrl': request.query_params.get(
            'downloadUrl', f"/api/v1/audit/exports/{generate_identifier('export')}"
        ),
        'estimatedCompletion': request.query_params.get('estimatedCompletion', isoformat_now()),
        'digitalSignature': request.query_params.get('digitalSignature', 'SIGNATURE'),
    }
    AuditExportRecord.objects.update_or_create(
        export_id=response['exportId'],
        defaults={
            'parameters': request.query_params.dict(),
            'status': response['status'],
            'download_url': response['downloadUrl'],
        },
    )
    return Response(response)


@api_view(['GET'])
def anomalies(request):
    anomalies_list = ensure_list(
        None,
        [
            {
                'type': request.query_params.get('type', 'unusual_access_pattern'),
                'userId': request.query_params.get('userId', generate_identifier('user')),
                'description': request.query_params.get(
                    'description', 'Access pattern requires review'
                ),
                'severity': request.query_params.get('severity', 'medium'),
                'timestamp': isoformat_now(),
                'score': float(request.query_params.get('score', 0.0)),
            }
        ],
    )
    for anomaly in anomalies_list:
        AuditAnomalyRecord.objects.update_or_create(
            anomaly_id=generate_identifier('anomaly'),
            defaults={
                'user_id': anomaly.get('userId', ''),
                'description': anomaly.get('description', ''),
                'severity': anomaly.get('severity', ''),
                'score': anomaly.get('score', 0.0),
                'data': anomaly,
            },
        )
    return Response({'period': request.query_params.get('period', 'P7D'), 'anomalies': anomalies_list})


urlpatterns = [
    path('events', log_event, name='events'),
    path('export', export_logs, name='export'),
    path('anomalies', anomalies, name='anomalies'),
]
