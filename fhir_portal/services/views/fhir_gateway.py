from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def get_patient(request, patient_id: str):
    return Response({
        'resourceType': 'Patient',
        'id': patient_id,
        'meta': {
            'versionId': '1',
            'lastUpdated': '2023-09-01T12:30:45Z',
        },
        'identifier': [
            {
                'use': 'usual',
                'value': 'MRN12345',
            }
        ],
    })


@api_view(['GET'])
def get_capability_statement(request):
    return Response({
        'resourceType': 'CapabilityStatement',
        'status': 'active',
        'date': '2023-09-01',
        'publisher': 'Healthcare Organization',
        'kind': 'instance',
        'software': {
            'name': 'FHIR Patient Portal',
            'version': '1.0.0',
        },
        'fhirVersion': '4.0.1',
        'format': ['json', 'xml'],
        'rest': [
            {
                'mode': 'server',
                'resource': [
                    {
                        'type': 'Patient',
                        'interaction': [
                            {'code': 'read'},
                            {'code': 'search-type'},
                        ],
                    }
                ],
            }
        ],
    })


@api_view(['POST'])
def batch_operations(request):
    return Response({
        'resourceType': 'Bundle',
        'type': 'batch-response',
        'entry': [
            {
                'response': {
                    'status': '200',
                    'location': 'Patient/patient-uuid-123',
                }
            },
            {
                'response': {
                    'status': '200',
                    'location': 'Observation?patient=patient-uuid-123',
                }
            },
        ],
    })
