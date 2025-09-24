from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import ensure_list, generate_identifier, isoformat_now


@api_view(['GET'])
def get_patient(request, patient_id: str):
    response = {
        'resourceType': 'Patient',
        'id': patient_id,
        'meta': {
            'versionId': request.query_params.get('versionId', '1'),
            'lastUpdated': isoformat_now(),
        },
        'identifier': ensure_list(
            request.query_params.getlist('identifier') or None,
            [{'use': 'usual', 'value': 'MRN-SAMPLE'}],
        ),
    }
    return Response(response)


@api_view(['GET'])
def get_capability_statement(request):
    response = {
        'resourceType': 'CapabilityStatement',
        'status': request.query_params.get('status', 'active'),
        'date': request.query_params.get('date', isoformat_now().split('T')[0]),
        'publisher': request.query_params.get('publisher', 'Healthcare Organization'),
        'kind': request.query_params.get('kind', 'instance'),
        'software': {
            'name': request.query_params.get('softwareName', 'FHIR Patient Portal'),
            'version': request.query_params.get('softwareVersion', '1.0.0'),
        },
        'fhirVersion': request.query_params.get('fhirVersion', '4.0.1'),
        'format': ensure_list(request.query_params.getlist('format'), ['json', 'xml']),
        'rest': ensure_list(
            None,
            [
                {
                    'mode': 'server',
                    'resource': [
                        {
                            'type': 'Patient',
                            'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                        }
                    ],
                }
            ],
        ),
    }
    return Response(response)


@api_view(['POST'])
def batch_operations(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'resourceType': 'Bundle',
        'type': payload.get('type', 'batch-response'),
        'entry': ensure_list(
            payload.get('entry'),
            [
                {
                    'response': {
                        'status': '200',
                        'location': f"Patient/{generate_identifier('patient')}",
                    }
                }
            ],
        ),
    }
    return Response(template)


urlpatterns = [
    path('Patient/<str:patient_id>', get_patient, name='fhir-get-patient'),
    path('metadata', get_capability_statement, name='fhir-metadata'),
    path('', batch_operations, name='fhir-batch'),
]
