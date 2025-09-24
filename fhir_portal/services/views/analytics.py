from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import (
    AnalyticsAlertConfiguration,
    AnalyticsFhirLinkRecord,
    AnalyticsRiskScore,
    AnalyticsTrainingJob,
    AnalyticsTrendRequest,
)
from ..sample_utils import deep_merge, ensure_list, generate_identifier, isoformat_now


@api_view(['POST'])
def risk_score(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'patientId': payload.get('patientId', generate_identifier('patient')),
        'riskType': payload.get('riskType', 'diabetes'),
        'score': float(payload.get('score', 0.75)),
        'level': payload.get('level', 'high'),
        'confidence': float(payload.get('confidence', 0.89)),
        'factors': ensure_list(payload.get('factors'), []),
        'recommendations': ensure_list(
            payload.get('recommendations'), ['Regular monitoring']
        ),
        'calculatedAt': payload.get('calculatedAt', isoformat_now()),
    }
    AnalyticsRiskScore.objects.update_or_create(
        patient_id=template['patientId'],
        risk_type=template['riskType'],
        defaults={
            'score': template['score'],
            'level': template['level'],
            'confidence': template['confidence'],
            'factors': template['factors'],
            'recommendations': template['recommendations'],
        },
    )
    return Response(template, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def train_model(request):
    payload = request.data if isinstance(request.data, dict) else {}
    job_payload = payload.get('trainingJob', payload)
    dataset_info = deep_merge(
        {
            'totalRecords': 0,
            'trainingRecords': 0,
            'validationRecords': 0,
            'testRecords': 0,
            'featureCount': 0,
            'classDistribution': {},
        },
        job_payload.get('datasetInfo', {}),
    )
    template = {
        'trainingJobId': generate_identifier('job', override=job_payload.get('trainingJobId')),
        'status': job_payload.get('status', 'running'),
        'estimatedCompletion': job_payload.get('estimatedCompletion', isoformat_now()),
        'datasetInfo': dataset_info,
        'progress': deep_merge(
            {'currentStep': 'pending', 'completionPercent': 0, 'estimatedTimeRemaining': None},
            job_payload.get('progress', {}),
        ),
    }
    AnalyticsTrainingJob.objects.update_or_create(
        training_job_id=template['trainingJobId'],
        defaults={
            'model_name': job_payload.get('modelName', ''),
            'model_type': job_payload.get('modelType', ''),
            'status': template['status'],
            'configuration': job_payload,
            'progress': template['progress'],
        },
    )
    return Response(template, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def personalized_alerts(request):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'alertId': generate_identifier('alert', override=payload.get('alertId')),
        'patientId': payload.get('patientId', generate_identifier('patient')),
        'riskAssessment': deep_merge(
            {
                'overallRisk': 0.0,
                'riskLevel': 'low',
                'confidence': 0.0,
                'prediction': {
                    'condition': 'unspecified',
                    'probability': 0.0,
                    'timeHorizon': 'P0D',
                },
            },
            payload.get('riskAssessment', {}),
        ),
        'contributingFactors': ensure_list(payload.get('contributingFactors'), []),
        'recommendations': ensure_list(payload.get('recommendations'), []),
        'fhirResources': ensure_list(payload.get('fhirResources'), []),
    }
    AnalyticsAlertConfiguration.objects.update_or_create(
        alert_id=template['alertId'],
        defaults={
            'patient_id': template['patientId'],
            'model_id': payload.get('modelId', ''),
            'configuration': payload.get('alertConfiguration', {}),
            'assessment': template['riskAssessment'],
        },
    )
    return Response(template, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def model_version(request, model_id: str):
    payload = request.data if isinstance(request.data, dict) else {}
    template = {
        'modelVersionId': generate_identifier('model-version', override=payload.get('modelVersionId')),
        'status': payload.get('status', 'deployed'),
        'deploymentTimestamp': payload.get('deploymentTimestamp', isoformat_now()),
        'performanceComparison': deep_merge(
            {
                'previousVersion': {},
                'improvement': {},
            },
            payload.get('performanceComparison', {}),
        ),
        'productionMetrics': deep_merge(
            {'predictionLatency': None, 'throughput': None, 'errorRate': None},
            payload.get('productionMetrics', {}),
        ),
        'modelId': model_id,
    }
    AnalyticsTrainingJob.objects.update_or_create(
        training_job_id=f"{model_id}:{template['modelVersionId']}",
        defaults={
            'model_name': model_id,
            'model_type': payload.get('modelType', ''),
            'status': template['status'],
            'configuration': payload.get('deploymentConfig', {}),
            'progress': template['productionMetrics'],
        },
    )
    return Response(template)


@api_view(['GET'])
def healthcare_trends(request):
    query = request.query_params
    time_range = {
        'start': query.get('start', isoformat_now()),
        'end': query.get('end', isoformat_now()),
    }
    metrics = query.getlist('metric')
    if metrics:
        trends = [
            {
                'metric': metric,
                'overall': {
                    'currentValue': float(query.get(f'{metric}.current', 0.0)),
                    'previousPeriod': float(query.get(f'{metric}.previous', 0.0)),
                    'changePercent': float(query.get(f'{metric}.changePercent', 0.0)),
                    'trend': query.get(f'{metric}.trend', 'stable'),
                    'significance': query.get(f'{metric}.significance', 'n/a'),
                },
                'byDemographics': [],
                'timeSeriesData': [],
            }
            for metric in metrics
        ]
    else:
        trends = [
            {
                'metric': 'readmission_rate',
                'overall': {
                    'currentValue': 0.0,
                    'previousPeriod': 0.0,
                    'changePercent': 0.0,
                    'trend': 'stable',
                    'significance': 'n/a',
                },
                'byDemographics': [],
                'timeSeriesData': [],
            }
        ]
    response = {
        'analysisId': query.get('analysisId', generate_identifier('trend-analysis')),
        'timeRange': time_range,
        'trends': trends,
        'correlations': ensure_list([], []),
        'anomalies': ensure_list([], []),
    }
    AnalyticsTrendRequest.objects.update_or_create(
        analysis_id=response['analysisId'],
        defaults={
            'parameters': query.dict(),
            'trends': trends,
            'correlations': response['correlations'],
            'anomalies': response['anomalies'],
        },
    )
    return Response(response)


@api_view(['POST'])
def link_fhir(request):
    payload = request.data if isinstance(request.data, dict) else {}
    default_resource = {
        'resourceType': 'RiskAssessment',
        'id': generate_identifier('risk-assessment'),
        'status': 'final',
        'subject': {'reference': f"Patient/{payload.get('patientId', generate_identifier('patient'))}"},
        'performer': {'reference': 'Device/ml-model-device'},
        'prediction': [
            {
                'outcome': {'coding': []},
                'probabilityDecimal': 0.0,
            }
        ],
    }
    template = {
        'linkingId': generate_identifier('fhir-link', override=payload.get('linkingId')),
        'fhirResources': ensure_list(payload.get('fhirResources'), [default_resource]),
        'auditTrail': deep_merge(
            {
                'createdBy': 'ml-system',
                'createdAt': isoformat_now(),
                'modelVersion': payload.get('modelId', '1.0.0'),
                'inputFeatures': payload.get('inputFeatures', 0),
                'confidence': payload.get('confidence', 0.0),
            },
            payload.get('auditTrail', {}),
        ),
    }
    AnalyticsFhirLinkRecord.objects.update_or_create(
        linking_id=template['linkingId'],
        defaults={
            'patient_id': payload.get('patientId', ''),
            'model_id': payload.get('modelId', ''),
            'fhir_resources': template['fhirResources'],
            'audit_trail': template['auditTrail'],
        },
    )
    return Response(template)


urlpatterns = [
    path('risk-score', risk_score, name='risk-score'),
    path('ml/models/train', train_model, name='train-model'),
    path('ml/alerts/personalized', personalized_alerts, name='personalized-alerts'),
    path('ml/models/<str:model_id>/versions', model_version, name='model-version'),
    path('analytics/trends', healthcare_trends, name='trends'),
    path('ml/predictions/link-fhir', link_fhir, name='link-fhir'),
]
