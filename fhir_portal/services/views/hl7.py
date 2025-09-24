from django.shortcuts import get_object_or_404
from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import HL7BatchRequest, HL7Message
from ..sample_utils import deep_merge, generate_identifier, isoformat_now, parse_iso_datetime


def _ingest_template() -> dict:
    return {
        'messageId': generate_identifier('msg'),
        'correlationId': generate_identifier('corr'),
        'status': 'processed',
        'timestamp': isoformat_now(),
        'fhirResources': [
            {
                'resourceType': 'Patient',
                'id': generate_identifier('patient'),
                'identifier': [{'value': 'MRN-PLACEHOLDER'}],
                'name': [{'family': 'Sample', 'given': ['Patient']}],
            }
        ],
        'errors': [],
    }


@api_view(['POST'])
def ingest(request):
    overrides = request.data if isinstance(request.data, dict) else {}
    template = deep_merge(_ingest_template(), overrides)
    raw_message = (
        request.body.decode('utf-8', errors='ignore').strip()
        or overrides.get('content')
        or overrides.get('rawMessage', '')
    )
    if not template.get('timestamp'):
        template['timestamp'] = isoformat_now()

    record, created = HL7Message.objects.update_or_create(
        message_id=template['messageId'],
        defaults={
            'correlation_id': template.get('correlationId', ''),
            'status': template.get('status', 'processed'),
            'raw_message': raw_message,
            'fhir_resources': template.get('fhirResources', []),
            'errors': template.get('errors', []),
            'processed_at': parse_iso_datetime(template.get('timestamp')),
        },
    )

    template['messageId'] = record.message_id
    template['correlationId'] = record.correlation_id
    template['errors'] = record.errors

    return Response(
        template,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(['GET'])
def parse_status(request, message_id: str):
    record = get_object_or_404(HL7Message, message_id=message_id)
    processed_at = record.processed_at.isoformat() if record.processed_at else isoformat_now()
    template = {
        'messageId': record.message_id,
        'status': request.query_params.get('status', record.status),
        'processedAt': processed_at,
        'resourcesCreated': int(
            request.query_params.get('resourcesCreated', len(record.fhir_resources or []))
        ),
        'errors': record.errors or [],
    }
    return Response(template)


@api_view(['POST'])
def batch(request):
    overrides = request.data if isinstance(request.data, dict) else {}
    template = {
        'batchId': overrides.get('batchId') or generate_identifier('batch'),
        'totalMessages': overrides.get('totalMessages', len(overrides.get('messages', []))),
        'processed': overrides.get('processed', 0),
        'failed': overrides.get('failed', 0),
        'processingTime': overrides.get('processingTime', '0s'),
        'status': overrides.get('status', 'pending'),
    }

    HL7BatchRequest.objects.update_or_create(
        batch_id=template['batchId'],
        defaults={
            'total_messages': template['totalMessages'],
            'processed': template['processed'],
            'failed': template['failed'],
            'processing_time': template['processingTime'],
            'payload': overrides,
        },
    )
    return Response(template, status=status.HTTP_202_ACCEPTED)


urlpatterns = [
    path('ingest', ingest, name='ingest'),
    path('parse-status/<str:message_id>', parse_status, name='parse-status'),
    path('batch', batch, name='batch'),
]
