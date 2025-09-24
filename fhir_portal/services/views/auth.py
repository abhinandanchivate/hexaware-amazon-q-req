from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import AuthEvent
from ..sample_utils import ensure_list, generate_identifier, isoformat_now


@api_view(['POST'])
def login(request):
    payload = request.data if isinstance(request.data, dict) else {}
    response = {
        'accessToken': payload.get('accessToken', generate_identifier('access-token')),
        'refreshToken': payload.get('refreshToken', generate_identifier('refresh-token')),
        'tokenType': payload.get('tokenType', 'Bearer'),
        'expiresIn': int(payload.get('expiresIn', 3600)),
        'user': {
            'id': payload.get('user', {}).get('id', generate_identifier('user')),
            'email': payload.get('username') or payload.get('email', 'user@example.com'),
            'roles': ensure_list(payload.get('roles'), ['patient']),
            'permissions': ensure_list(
                payload.get('permissions'), ['read:own_records', 'write:own_profile']
            ),
        },
        'issuedAt': isoformat_now(),
    }
    AuthEvent.objects.create(
        user_id=response['user']['id'],
        event_type='login',
        username=response['user']['email'],
        device_info=payload.get('deviceInfo', {}),
        metadata={'mfaCode': payload.get('mfaCode')},
    )
    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
def register(request):
    payload = request.data if isinstance(request.data, dict) else {}
    response = {
        'status': payload.get('status', 'registered'),
        'userId': generate_identifier('user', override=payload.get('userId')),
        'verificationMethod': payload.get('verificationMethod', 'email'),
    }
    AuthEvent.objects.create(
        user_id=response['userId'],
        event_type='register',
        username=payload.get('email', ''),
        metadata={'profile': payload.get('profile', {}), 'acceptTerms': payload.get('acceptTerms')},
    )
    return Response(response, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def password_reset(request):
    payload = request.data if isinstance(request.data, dict) else {}
    response = {
        'status': payload.get('status', 'sent'),
        'message': payload.get(
            'message', 'Password reset instructions sent to email'
        ),
        'resetTokenId': generate_identifier('reset', override=payload.get('resetTokenId')),
        'expiresIn': int(payload.get('expiresIn', 3600)),
    }
    AuthEvent.objects.create(
        user_id=payload.get('userId', response['resetTokenId']),
        event_type='password_reset',
        username=payload.get('email', ''),
        metadata={'resetMethod': payload.get('resetMethod')},
    )
    return Response(response)


@api_view(['POST'])
def mfa_setup(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'qrCode': payload.get('qrCode', 'data:image/png;base64,PLACEHOLDER'),
        'secret': payload.get('secret', 'SAMPLESECRET'),
        'backupCodes': ensure_list(payload.get('backupCodes'), ['12345678', '87654321']),
    }
    AuthEvent.objects.create(
        user_id=payload.get('userId', generate_identifier('user')),
        event_type='mfa_setup',
        username=payload.get('email', ''),
        metadata={'method': payload.get('method'), 'deviceName': payload.get('deviceName')},
    )
    return Response(template)


urlpatterns = [
    path('login', login, name='login'),
    path('register', register, name='register'),
    path('password-reset', password_reset, name='password-reset'),
    path('mfa/setup', mfa_setup, name='mfa-setup'),
]
