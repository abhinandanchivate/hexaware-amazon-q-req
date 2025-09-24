from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def login(request):
    return Response({
        'accessToken': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        'refreshToken': 'refresh-token-uuid',
        'tokenType': 'Bearer',
        'expiresIn': 3600,
        'user': {
            'id': 'user-uuid-123',
            'email': 'john.doe@example.com',
            'roles': ['patient'],
            'permissions': ['read:own_records', 'write:own_profile'],
        },
    })


@api_view(['POST'])
def register(request):
    return Response({
        'status': 'registered',
        'userId': 'user-uuid-123',
        'verificationMethod': request.data.get('verificationMethod', 'email'),
    })


@api_view(['POST'])
def password_reset(request):
    return Response({
        'status': 'sent',
        'message': 'Password reset instructions sent to email',
        'resetTokenId': 'reset-uuid-123',
        'expiresIn': 3600,
    })


@api_view(['POST'])
def mfa_setup(request):
    return Response({
        'qrCode': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...',
        'secret': 'JBSWY3DPEHPK3PXP',
        'backupCodes': ['12345678', '87654321'],
    })


urlpatterns = [
    path('login', login, name='login'),
    path('register', register, name='register'),
    path('password-reset', password_reset, name='password-reset'),
    path('mfa/setup', mfa_setup, name='mfa-setup'),
]
