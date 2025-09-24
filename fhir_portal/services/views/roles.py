from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import AbacEvaluationRecord, RoleAssignmentRecord
from ..sample_utils import ensure_list, generate_identifier, isoformat_now, parse_iso_datetime


@api_view(['POST'])
def assign(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'assignmentId': generate_identifier('assignment', override=payload.get('assignmentId')),
        'status': payload.get('status', 'active'),
        'permissions': ensure_list(
            payload.get('permissions'),
            ['read:patient_records', 'write:observations', 'manage:department_users'],
        ),
        'effectiveDate': payload.get('effectiveDate', isoformat_now()),
        'expiryDate': payload.get('expiryDate'),
    }
    RoleAssignmentRecord.objects.update_or_create(
        assignment_id=template['assignmentId'],
        defaults={
            'user_id': payload.get('userId', ''),
            'roles': ensure_list(payload.get('roles'), []),
            'permissions': template['permissions'],
            'effective_date': parse_iso_datetime(template['effectiveDate']),
            'expiry_date': parse_iso_datetime(template['expiryDate']),
            'reason': payload.get('reason', ''),
        },
    )
    return Response(template, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def validate(request):
    payload = request.data if isinstance(request.data, dict) else {}
    decision = payload.get('decision', 'permit')
    response = {
        'allowed': bool(payload.get('allowed', True)),
        'decision': decision,
        'reason': payload.get(
            'reason', 'User has appropriate role with required permission'
        ),
        'conditions': ensure_list(payload.get('conditions'), ['audit_required']),
    }
    AbacEvaluationRecord.objects.create(
        user_id=payload.get('userId', ''),
        resource_type=payload.get('resourceType', ''),
        resource_id=payload.get('resource', ''),
        action=payload.get('action', 'read'),
        decision=decision,
        context=payload.get('context', {}),
    )
    return Response(response)


@api_view(['POST'])
def abac(request):
    payload = request.data if isinstance(request.data, dict) else {}
    decision = payload.get('decision', 'permit')
    response = {
        'decision': decision,
        'explanation': payload.get(
            'explanation',
            'Subject, resource, and environment attributes satisfy policy rules',
        ),
        'obligations': ensure_list(
            payload.get('obligations'), ['log_access', 'session_timeout']
        ),
        'evaluatedAt': isoformat_now(),
    }
    AbacEvaluationRecord.objects.create(
        user_id=payload.get('subject', {}).get('userId', ''),
        resource_type=payload.get('resource', {}).get('type', ''),
        resource_id=payload.get('resource', {}).get('id', ''),
        action=payload.get('action', 'read'),
        decision=decision,
        context={
            'subject': payload.get('subject', {}),
            'resource': payload.get('resource', {}),
            'environment': payload.get('environment', {}),
        },
    )
    return Response(response)


urlpatterns = [
    path('assign', assign, name='assign'),
    path('validate', validate, name='validate'),
    path('abac/evaluate', abac, name='abac'),
]
