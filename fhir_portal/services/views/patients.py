from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


PATIENT_SAMPLE = {
    'resourceType': 'Patient',
    'id': 'patient-uuid-123',
    'meta': {
        'versionId': '1',
        'lastUpdated': '2023-09-01T12:30:45Z',
    },
    'identifier': [
        {
            'use': 'usual',
            'type': {
                'coding': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'MR',
                    }
                ]
            },
            'value': 'MRN12345',
        }
    ],
    'name': [
        {
            'use': 'official',
            'family': 'Doe',
            'given': ['John', 'Michael'],
        }
    ],
    'gender': 'male',
    'birthDate': '1980-01-15',
}


@api_view(['POST'])
def register(request):
    return Response(PATIENT_SAMPLE)


@api_view(['PUT'])
def update(request, patient_id: str):
    updated = PATIENT_SAMPLE.copy()
    updated['id'] = patient_id
    updated['meta'] = {
        'versionId': '2',
        'lastUpdated': '2023-09-02T10:15:00Z',
    }
    return Response(updated)


@api_view(['GET'])
def search(request):
    return Response({
        'resourceType': 'Bundle',
        'type': 'searchset',
        'total': 1,
        'entry': [
            {
                'resource': {
                    'resourceType': 'Patient',
                    'id': 'patient-uuid-123',
                    'name': [{'family': 'Doe', 'given': ['John']}],
                }
            }
        ],
    })


@api_view(['POST'])
def merge(request, source_id: str, target_id: str):
    return Response({
        'status': 'merged',
        'resultPatientId': target_id,
        'mergedFields': ['telecom', 'address'],
        'auditId': 'audit-uuid-456',
    })


@api_view(['GET'])
def export(request, patient_id: str):
    return Response({
        'exportId': 'export-uuid-789',
        'status': 'completed',
        'downloadUrl': f'/api/v1/exports/export-uuid-789/download',
        'format': request.query_params.get('format', 'pdf'),
        'size': '2.4MB',
        'expiresAt': '2023-09-08T12:30:45Z',
    })


urlpatterns = [
    path('', register, name='register'),
    path('search', search, name='search'),
    path('<str:source_id>/merge/<str:target_id>', merge, name='merge'),
    path('<str:patient_id>/export', export, name='export'),
    path('<str:patient_id>', update, name='update'),
]
