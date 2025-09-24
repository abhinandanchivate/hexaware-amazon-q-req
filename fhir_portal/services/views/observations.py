from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import deep_merge, ensure_list, generate_identifier, isoformat_now


def _observation_template(payload: dict | None = None) -> dict:
    payload = payload or {}
    return {
        'resourceType': payload.get('resourceType', 'Observation'),
        'id': generate_identifier('obs', override=payload.get('id')),
        'meta': {
            'versionId': payload.get('meta', {}).get('versionId', '1'),
            'lastUpdated': isoformat_now(),
        },
        'status': payload.get('status', 'final'),
        'category': ensure_list(
            payload.get('category'),
            [
                {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                            'code': 'vital-signs',
                        }
                    ]
                }
            ],
        ),
    }


@api_view(['POST'])
def create_vital_sign(request):
    payload = request.data if isinstance(request.data, dict) else {}
    return Response(deep_merge(_observation_template(payload), payload))


@api_view(['POST'])
def lab_results(request):
    payload = request.data if isinstance(request.data, dict) else {}
    bundle_template = {
        'resourceType': 'Bundle',
        'type': payload.get('type', 'transaction-response'),
        'entry': ensure_list(
            payload.get('entry'),
            [
                {
                    'response': {
                        'status': '201 Created',
                        'location': f"Observation/{generate_identifier('obs')}",
                    }
                }
            ],
        ),
    }
    return Response(bundle_template)


@api_view(['GET'])
def trends(request, patient_id: str):
    query = request.query_params
    time_range = {
        'start': query.get('start', isoformat_now()),
        'end': query.get('end', isoformat_now()),
    }
    data_points = ensure_list(
        None,
        [
            {
                'timestamp': isoformat_now(),
                'value': float(query.get('value', 0)),
                'status': query.get('status', 'normal'),
            }
        ],
    )
    response = {
        'patientId': patient_id,
        'observationType': query.get('observationType', 'glucose'),
        'unit': query.get('unit', 'mg/dL'),
        'timeRange': time_range,
        'dataPoints': data_points,
        'referenceRanges': {
            'low': float(query.get('low', 0)),
            'high': float(query.get('high', 0)),
        },
    }
    return Response(response)


@api_view(['POST'])
def configure_alert(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'patientId': payload.get('patientId', generate_identifier('patient')),
        'observationCode': payload.get('observationCode', 'unknown'),
        'status': payload.get('status', 'configured'),
        'notificationChannels': ensure_list(
            payload.get('notificationChannels'), ['email', 'sms']
        ),
    }
    return Response(template)


urlpatterns = [
    path('', create_vital_sign, name='create'),
    path('lab-results', lab_results, name='lab-results'),
    path('<str:patient_id>/trends', trends, name='trends'),
    path('alerts/configure', configure_alert, name='configure-alert'),
]
