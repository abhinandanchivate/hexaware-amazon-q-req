from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

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
    return Response(response)


@api_view(['POST'])
def register(request):
    payload = request.data if isinstance(request.data, dict) else {}
    return Response(
        {
            'status': payload.get('status', 'registered'),
            'userId': generate_identifier('user', override=payload.get('userId')),
            'verificationMethod': payload.get('verificationMethod', 'email'),
        }
    )


@api_view(['POST'])
def password_reset(request):
    payload = request.data if isinstance(request.data, dict) else {}
    return Response(
        {
            'status': payload.get('status', 'sent'),
            'message': payload.get(
                'message', 'Password reset instructions sent to email'
            ),
            'resetTokenId': generate_identifier('reset', override=payload.get('resetTokenId')),
            'expiresIn': int(payload.get('expiresIn', 3600)),
        }
    )


@api_view(['POST'])
def mfa_setup(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'qrCode': payload.get('qrCode', 'data:image/png;base64,PLACEHOLDER'),
        'secret': payload.get('secret', 'SAMPLESECRET'),
        'backupCodes': ensure_list(payload.get('backupCodes'), ['12345678', '87654321']),
    }
    return Response(template)


urlpatterns = [
    path('login', login, name='login'),
    path('register', register, name='register'),
    path('password-reset', password_reset, name='password-reset'),
    path('mfa/setup', mfa_setup, name='mfa-setup'),
]
