from django.db.models import Q
from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import PatientExportJob, PatientMergeEvent, PatientRecord
from ..sample_utils import (
    deep_merge,
    ensure_list,
    generate_identifier,
    isoformat_now,
    parse_iso_date,
    parse_iso_datetime,
)


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
    template = deep_merge(_patient_template(payload), payload)
    names = template.get('name', [])
    primary_name = names[0] if names else {}
    identifier_entries = template.get('identifier', [])
    identifier_value = ''
    if identifier_entries:
        identifier_value = identifier_entries[0].get('value', '')
    full_name_parts = []
    if primary_name.get('family'):
        full_name_parts.append(primary_name['family'])
    full_name_parts.extend(primary_name.get('given', []))
    full_name = ' '.join(part for part in full_name_parts if part)

    record, created = PatientRecord.objects.update_or_create(
        patient_id=template['id'],
        defaults={
            'identifier': identifier_value,
            'name': full_name,
            'birth_date': parse_iso_date(template.get('birthDate')),
            'gender': template.get('gender', 'unknown'),
            'data': template,
        },
    )

    template['id'] = record.patient_id

    return Response(
        template,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(['PUT'])
def update(request, patient_id: str):
    payload = request.data if isinstance(request.data, dict) else {}
    template = _patient_template({**payload, 'id': patient_id})
    template['meta']['versionId'] = payload.get('meta', {}).get('versionId', '2')
    merged = deep_merge(template, payload)
    names = merged.get('name', [])
    primary_name = names[0] if names else {}
    identifier_entries = merged.get('identifier', [])
    identifier_value = ''
    if identifier_entries:
        identifier_value = identifier_entries[0].get('value', '')
    full_name_parts = []
    if primary_name.get('family'):
        full_name_parts.append(primary_name['family'])
    full_name_parts.extend(primary_name.get('given', []))
    full_name = ' '.join(part for part in full_name_parts if part)

    PatientRecord.objects.update_or_create(
        patient_id=patient_id,
        defaults={
            'identifier': identifier_value,
            'name': full_name,
            'birth_date': parse_iso_date(merged.get('birthDate')),
            'gender': merged.get('gender', 'unknown'),
            'data': merged,
        },
    )

    return Response(merged)


@api_view(['GET'])
def search(request):
    query = request.query_params
    records = PatientRecord.objects.all()

    identifier = query.get('identifier')
    if identifier:
        records = records.filter(identifier__icontains=identifier)

    name_filters = query.getlist('name')
    if name_filters:
        name_query = Q()
        for value in name_filters:
            name_query |= Q(name__icontains=value)
        records = records.filter(name_query)

    birth_date = query.get('birthdate')
    if birth_date:
        parsed_birth_date = parse_iso_date(birth_date)
        if parsed_birth_date:
            records = records.filter(birth_date=parsed_birth_date)

    if query.get('gender'):
        records = records.filter(gender__iexact=query['gender'])

    entries = [
        {'resource': record.data or {'resourceType': 'Patient', 'id': record.patient_id}}
        for record in records
    ]

    if not entries:
        default_patient = _patient_template()
        entries.append({'resource': default_patient})

    response = {
        'resourceType': 'Bundle',
        'type': 'searchset',
        'total': len(entries),
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
    PatientMergeEvent.objects.create(
        source_patient_id=source_id,
        target_patient_id=target_id,
        reason=payload.get('reason', ''),
        merge_strategy=payload.get('mergeStrategy', ''),
        merged_fields=template['mergedFields'],
        audit_reason=payload.get('auditReason', ''),
    )
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
    PatientExportJob.objects.update_or_create(
        export_id=template['exportId'],
        defaults={
            'patient_id': patient_id,
            'status': template['status'],
            'format': template['format'],
            'include_sections': request.query_params.getlist('includeSections'),
            'download_url': template['downloadUrl'],
            'expires_at': parse_iso_datetime(template['expiresAt']),
        },
    )
    return Response(template)


urlpatterns = [
    path('', register, name='register'),
    path('search', search, name='search'),
    path('<str:source_id>/merge/<str:target_id>', merge, name='merge'),
    path('<str:patient_id>/export', export, name='export'),
    path('<str:patient_id>', update, name='update'),
]
