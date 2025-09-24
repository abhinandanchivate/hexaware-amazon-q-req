from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import deep_merge, generate_identifier, isoformat_now


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
    return Response(deep_merge(_ingest_template(), overrides))


@api_view(['GET'])
def parse_status(request, message_id: str):
    template = {
        'messageId': message_id,
        'status': request.query_params.get('status', 'completed'),
        'processedAt': isoformat_now(),
        'resourcesCreated': int(request.query_params.get('resourcesCreated', 3)),
        'errors': [],
    }
    return Response(template)


@api_view(['POST'])
def batch(request):
    overrides = request.data if isinstance(request.data, dict) else {}
    template = {
        'batchId': overrides.get('batchId') or generate_identifier('batch'),
        'totalMessages': overrides.get('totalMessages', 0),
        'processed': overrides.get('processed', 0),
        'failed': overrides.get('failed', 0),
        'processingTime': overrides.get('processingTime', '0s'),
        'status': overrides.get('status', 'pending'),
    }
    return Response(template)


urlpatterns = [
    path('ingest', ingest, name='ingest'),
    path('parse-status/<str:message_id>', parse_status, name='parse-status'),
    path('batch', batch, name='batch'),
]
