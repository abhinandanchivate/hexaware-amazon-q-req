from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import ObservationAlertConfig, ObservationRecord
from ..sample_utils import (
    deep_merge,
    ensure_list,
    generate_identifier,
    isoformat_now,
    parse_iso_datetime,
)


def _extract_quantity(payload: dict) -> float | None:
    value_quantity = payload.get('valueQuantity')
    if isinstance(value_quantity, dict):
        return value_quantity.get('value')
    components = payload.get('component') or []
    if components:
        first_component = components[0]
        value_quantity = first_component.get('valueQuantity')
        if isinstance(value_quantity, dict):
            return value_quantity.get('value')
    return None


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
    merged = deep_merge(_observation_template(payload), payload)
    record, created = ObservationRecord.objects.update_or_create(
        observation_id=merged['id'],
        defaults={
            'patient_reference': merged.get('subject', {}).get('reference', ''),
            'category': ensure_list(merged.get('category'), [{}])[0]
            .get('coding', [{}])[0]
            .get('code', ''),
            'code': merged.get('code', {}).get('coding', [{}])[0].get('code', ''),
            'status': merged.get('status', 'final'),
            'effective_datetime': parse_iso_datetime(merged.get('effectiveDateTime')),
            'data': merged,
        },
    )
    merged['id'] = record.observation_id
    return Response(
        merged,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


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
    for entry in payload.get('entry', []):
        resource = entry.get('resource')
        if not isinstance(resource, dict) or resource.get('resourceType') != 'Observation':
            continue
        observation_id = resource.get('id') or generate_identifier('obs')
        ObservationRecord.objects.update_or_create(
            observation_id=observation_id,
            defaults={
                'patient_reference': resource.get('subject', {}).get('reference', ''),
                'category': ensure_list(resource.get('category'), [{}])[0]
                .get('coding', [{}])[0]
                .get('code', ''),
                'code': resource.get('code', {}).get('coding', [{}])[0].get('code', ''),
                'status': resource.get('status', 'final'),
                'effective_datetime': parse_iso_datetime(resource.get('effectiveDateTime')),
                'data': resource,
            },
        )
    return Response(bundle_template)


@api_view(['GET'])
def trends(request, patient_id: str):
    query = request.query_params
    records = ObservationRecord.objects.filter(patient_reference__icontains=patient_id)

    code = query.get('code')
    if code:
        records = records.filter(code__iexact=code)

    category = query.get('category')
    if category:
        records = records.filter(category__iexact=category)

    time_range = {
        'start': query.get('start', isoformat_now()),
        'end': query.get('end', isoformat_now()),
    }

    data_points = []
    for record in records:
        value = _extract_quantity(record.data or {})
        data_points.append(
            {
                'timestamp': record.effective_datetime.isoformat()
                if record.effective_datetime
                else isoformat_now(),
                'value': value,
                'status': record.status or 'unknown',
            }
        )

    if not data_points:
        data_points = ensure_list(
            None,
            [
                {
                    'timestamp': isoformat_now(),
                    'value': float(query.get('value', 0) or 0),
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
    patient_id = payload.get('patientId', generate_identifier('patient'))
    observation_code = payload.get('observationCode', 'unknown')
    notification_channels = ensure_list(
        payload.get('notificationChannels'), ['email', 'sms', 'app']
    )
    record, _ = ObservationAlertConfig.objects.update_or_create(
        patient_id=patient_id,
        observation_code=observation_code,
        defaults={
            'thresholds': payload.get('thresholds', {}),
            'notification_channels': notification_channels,
            'active': bool(payload.get('active', True)),
        },
    )
    template = {
        'patientId': record.patient_id,
        'observationCode': record.observation_code,
        'status': 'configured' if record.active else 'disabled',
        'notificationChannels': notification_channels,
    }
    return Response(template)


urlpatterns = [
    path('', create_vital_sign, name='create'),
    path('lab-results', lab_results, name='lab-results'),
    path('<str:patient_id>/trends', trends, name='trends'),
    path('alerts/configure', configure_alert, name='configure-alert'),
]
