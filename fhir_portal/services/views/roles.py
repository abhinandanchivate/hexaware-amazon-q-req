from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import ensure_list, generate_identifier, isoformat_now


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
    return Response(template)


@api_view(['POST'])
def validate(request):
    payload = request.data if isinstance(request.data, dict) else {}
    return Response(
        {
            'allowed': bool(payload.get('allowed', True)),
            'decision': payload.get('decision', 'permit'),
            'reason': payload.get(
                'reason', 'User has appropriate role with required permission'
            ),
            'conditions': ensure_list(payload.get('conditions'), ['audit_required']),
        }
    )


@api_view(['POST'])
def abac(request):
    payload = request.data if isinstance(request.data, dict) else {}
    return Response(
        {
            'decision': payload.get('decision', 'permit'),
            'explanation': payload.get(
                'explanation',
                'Subject, resource, and environment attributes satisfy policy rules',
            ),
            'obligations': ensure_list(
                payload.get('obligations'), ['log_access', 'session_timeout']
            ),
            'evaluatedAt': isoformat_now(),
        }
    )


urlpatterns = [
    path('assign', assign, name='assign'),
    path('validate', validate, name='validate'),
    path('abac/evaluate', abac, name='abac'),
]
