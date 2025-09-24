from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def assign(request):
    return Response({
        'assignmentId': 'assignment-uuid-789',
        'status': 'active',
        'permissions': [
            'read:patient_records',
            'write:observations',
            'manage:department_users',
        ],
        'effectiveDate': '2023-09-01T00:00:00Z',
    })


@api_view(['POST'])
def validate(request):
    return Response({
        'allowed': True,
        'decision': 'permit',
        'reason': 'User has doctor role with read permission',
        'conditions': ['audit_required', 'time_limited'],
    })


@api_view(['POST'])
def abac(request):
    return Response({
        'decision': 'permit',
        'explanation': 'Subject, resource, and environment attributes satisfy policy rules',
        'obligations': ['log_access', 'session_timeout'],
    })


urlpatterns = [
    path('assign', assign, name='assign'),
    path('validate', validate, name='validate'),
    path('abac/evaluate', abac, name='abac'),
]
