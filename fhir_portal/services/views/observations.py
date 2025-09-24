from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def create_vital_sign(request):
    return Response({
        'resourceType': 'Observation',
        'id': 'obs-uuid-123',
        'meta': {
            'versionId': '1',
            'lastUpdated': '2023-09-01T12:30:45Z',
        },
        'status': 'final',
        'category': [
            {
                'coding': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                        'code': 'vital-signs',
                    }
                ]
            }
        ],
    })


@api_view(['POST'])
def lab_results(request):
    return Response({
        'resourceType': 'Bundle',
        'type': 'transaction-response',
        'entry': [
            {
                'response': {
                    'status': '201 Created',
                    'location': 'Observation/obs-uuid-456',
                }
            }
        ],
    })


@api_view(['GET'])
def trends(request, patient_id: str):
    return Response({
        'patientId': patient_id,
        'observationType': 'glucose',
        'unit': 'mg/dL',
        'timeRange': {
            'start': '2023-08-01T00:00:00Z',
            'end': '2023-09-01T00:00:00Z',
        },
        'dataPoints': [
            {
                'timestamp': '2023-08-01T08:00:00Z',
                'value': 95,
                'status': 'normal',
            },
            {
                'timestamp': '2023-08-15T08:00:00Z',
                'value': 110,
                'status': 'high',
            },
        ],
        'referenceRanges': {
            'low': 70,
            'high': 100,
        },
    })


@api_view(['POST'])
def configure_alert(request):
    return Response({
        'patientId': request.data.get('patientId', 'patient-uuid-123'),
        'observationCode': request.data.get('observationCode', '8480-6'),
        'status': 'configured',
        'notificationChannels': request.data.get('notificationChannels', ['email']),
    })


urlpatterns = [
    path('', create_vital_sign, name='create'),
    path('lab-results', lab_results, name='lab-results'),
    path('<str:patient_id>/trends', trends, name='trends'),
    path('alerts/configure', configure_alert, name='configure-alert'),
]
