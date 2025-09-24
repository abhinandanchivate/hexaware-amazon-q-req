from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import deep_merge, ensure_list, generate_identifier, isoformat_now


def _patient_template(payload: dict | None = None) -> dict:
    payload = payload or {}
    identifiers = ensure_list(
        payload.get('identifier'),
        [
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
                'value': 'MRN-SAMPLE',
            }
        ],
    )
    names = ensure_list(
        payload.get('name'),
        [
            {
                'use': 'official',
                'family': 'Sample',
                'given': ['Patient'],
            }
        ],
    )
    return {
        'resourceType': 'Patient',
        'id': generate_identifier('patient', override=payload.get('id')),
        'meta': {
            'versionId': payload.get('meta', {}).get('versionId', '1'),
            'lastUpdated': isoformat_now(),
        },
        'identifier': identifiers,
        'name': names,
        'gender': payload.get('gender', 'unknown'),
        'birthDate': payload.get('birthDate', '1970-01-01'),
    }


@api_view(['POST'])
def register(request):
    payload = request.data if isinstance(request.data, dict) else {}
    return Response(deep_merge(_patient_template(payload), payload))


@api_view(['PUT'])
def update(request, patient_id: str):
    payload = request.data if isinstance(request.data, dict) else {}
    template = _patient_template({**payload, 'id': patient_id})
    template['meta']['versionId'] = payload.get('meta', {}).get('versionId', '2')
    return Response(deep_merge(template, payload))


@api_view(['GET'])
def search(request):
    name_query = request.query_params.getlist('name')
    if name_query:
        names = [{'text': value} for value in name_query]
    else:
        names = [{'family': 'Sample', 'given': ['Patient']}]
    entries = [
        {
            'resource': {
                'resourceType': 'Patient',
                'id': request.query_params.get('id', generate_identifier('patient')),
                'name': names,
            }
        }
    ]
    response = {
        'resourceType': 'Bundle',
        'type': 'searchset',
        'total': int(request.query_params.get('total', len(entries))),
        'entry': entries,
    }
    return Response(response)


@api_view(['POST'])
def merge(request, source_id: str, target_id: str):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'status': payload.get('status', 'merged'),
        'resultPatientId': target_id,
        'mergedFields': payload.get('mergedFields', ['telecom', 'address']),
        'auditId': generate_identifier('audit', override=payload.get('auditId')),
    }
    return Response(template)


@api_view(['GET'])
def export(request, patient_id: str):
    template = {
        'exportId': generate_identifier('export'),
        'status': request.query_params.get('status', 'completed'),
        'downloadUrl': request.query_params.get(
            'downloadUrl', f'/api/v1/exports/{generate_identifier("export")}/download'
        ),
        'format': request.query_params.get('format', 'pdf'),
        'size': request.query_params.get('size', '0MB'),
        'expiresAt': request.query_params.get('expiresAt', isoformat_now()),
    }
    return Response(template)


urlpatterns = [
    path('', register, name='register'),
    path('search', search, name='search'),
    path('<str:source_id>/merge/<str:target_id>', merge, name='merge'),
    path('<str:patient_id>/export', export, name='export'),
    path('<str:patient_id>', update, name='update'),
]
