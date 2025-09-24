from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def ingest(request):
    sample_message = {
        'messageId': 'MSG001',
        'correlationId': 'corr-uuid-123',
        'status': 'processed',
        'timestamp': '2023-09-01T12:30:45Z',
        'fhirResources': [
            {
                'resourceType': 'Patient',
                'id': 'patient-12345',
                'identifier': [{'value': 'MRN12345'}],
                'name': [{'family': 'Doe', 'given': ['John']}],
            }
        ],
        'errors': [],
    }
    return Response(sample_message)


@api_view(['GET'])
def parse_status(request, message_id: str):
    return Response({
        'messageId': message_id,
        'status': 'completed',
        'processedAt': '2023-09-01T12:30:45Z',
        'resourcesCreated': 3,
        'errors': [],
    })


@api_view(['POST'])
def batch(request):
    return Response({
        'batchId': request.data.get('batchId', 'batch-001'),
        'totalMessages': 10,
        'processed': 8,
        'failed': 2,
        'processingTime': '45.2s',
        'status': 'partial_success',
    })


urlpatterns = [
    path('ingest', ingest, name='ingest'),
    path('parse-status/<str:message_id>', parse_status, name='parse-status'),
    path('batch', batch, name='batch'),
]
