from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..sample_utils import deep_merge, ensure_list


def _base_event_template() -> dict:
    return {
        "eventId": "event-uuid-sample",
        "eventType": "patient.registered.v1",
        "eventVersion": "1.0",
        "timestamp": "2023-09-01T12:30:45Z",
        "source": {
            "service": "patient-service",
            "version": "2.1.0",
            "instance": "patient-service-pod-3",
        },
        "subject": {
            "type": "Patient",
            "id": "patient-uuid-123",
            "tenantId": "tenant-clinic-001",
        },
        "data": {
            "action": "created",
            "userId": "user-uuid-456",
            "previousState": None,
            "currentState": {
                "status": "active",
                "registrationComplete": True,
            },
        },
        "metadata": {
            "correlationId": "corr-uuid-789",
            "causationId": "cause-uuid-101",
            "sessionId": "session-uuid-202",
            "traceId": "trace-uuid-303",
            "priority": "normal",
            "retryCount": 0,
        },
        "compliance": {
            "dataClassification": "PHI",
            "retentionPeriod": "P7Y",
            "encryptionRequired": True,
            "auditRequired": True,
        },
    }


def _topic_configuration_template() -> dict:
    return {
        "patient.lifecycle.v1": {
            "partitions": 12,
            "replicationFactor": 3,
            "retentionMs": 604800000,
            "partitionKey": "patientId",
            "compressionType": "lz4",
            "cleanupPolicy": "delete",
            "messageTypes": ensure_list(
                None,
                [
                    "patient.registered.v1",
                    "patient.updated.v1",
                    "patient.merged.v1",
                    "patient.anonymized.v1",
                    "patient.consent.changed.v1",
                ],
            ),
        },
        "patient.search.v1": {
            "partitions": 6,
            "replicationFactor": 3,
            "retentionMs": 86400000,
            "partitionKey": "searchHash",
            "compressionType": "snappy",
            "cleanupPolicy": "delete",
        },
        "observation.clinical.v1": {
            "partitions": 24,
            "replicationFactor": 3,
            "retentionMs": 2592000000,
            "partitionKey": "patientId",
            "compressionType": "lz4",
            "messageTypes": ensure_list(
                None,
                [
                    "observation.created.v1",
                    "observation.updated.v1",
                    "observation.alert.triggered.v1",
                    "observation.batch.processed.v1",
                ],
            ),
        },
        "appointment.scheduling.v1": {
            "partitions": 8,
            "replicationFactor": 3,
            "retentionMs": 1209600000,
            "partitionKey": "practitionerId",
            "compressionType": "lz4",
        },
        "security.events.v1": {
            "partitions": 16,
            "replicationFactor": 3,
            "retentionMs": 31536000000,
            "partitionKey": "userId",
            "compressionType": "gzip",
            "cleanupPolicy": "compact",
        },
        "audit.trail.v1": {
            "partitions": 32,
            "replicationFactor": 3,
            "retentionMs": 220752000000,
            "partitionKey": "resourceId",
            "compressionType": "gzip",
            "cleanupPolicy": "compact",
        },
        "dlq.failed-events.v1": {
            "partitions": 4,
            "replicationFactor": 3,
            "retentionMs": 604800000,
            "compressionType": "gzip",
            "retryPolicy": {
                "maxRetries": 3,
                "backoffStrategy": "exponential",
                "initialDelay": "PT1S",
                "maxDelay": "PT30S",
                "jitterEnabled": True,
            },
            "alerting": {
                "enabled": True,
                "threshold": 100,
                "timeWindow": "PT1H",
                "channels": ["slack", "email"],
            },
        },
    }


def _partitioning_strategy_template() -> dict:
    return {
        "patient.lifecycle.v1": {
            "partitionKey": "data.patientId",
            "keyExtractor": "$.subject.id",
            "orderingGuarantee": "per_patient",
        },
        "observation.clinical.v1": {
            "partitionKey": "data.patientId",
            "keyExtractor": "$.data.subject.reference",
            "orderingGuarantee": "per_patient_per_observation_type",
        },
        "appointment.scheduling.v1": {
            "partitionKey": "data.practitionerId",
            "orderingGuarantee": "per_practitioner",
        },
        "audit.trail.v1": {
            "partitionKey": "data.resourceId",
            "orderingGuarantee": "per_resource",
        },
    }


def _consumer_groups_template() -> dict:
    return {
        "realtime": ensure_list(
            None,
            [
                {
                    "groupId": "patient-service-realtime",
                    "topics": [
                        "hl7.message.received.v1",
                        "user.registered.v1",
                        "consent.updated.v1",
                    ],
                    "processingMode": "exactly_once",
                    "maxPollRecords": 100,
                    "sessionTimeoutMs": 30000,
                    "autoCommit": False,
                },
                {
                    "groupId": "notification-service-immediate",
                    "topics": [
                        "appointment.booked.v1",
                        "observation.alert.triggered.v1",
                        "security.alert.triggered.v1",
                    ],
                    "processingMode": "at_least_once",
                    "maxPollRecords": 50,
                    "priorityQueues": {
                        "critical": ["security.alert.triggered.v1"],
                        "high": ["observation.alert.triggered.v1"],
                        "normal": ["appointment.booked.v1"],
                    },
                },
            ],
        ),
        "batch": [
            {
                "groupId": "analytics-service-batch",
                "topics": [
                    "patient.lifecycle.v1",
                    "observation.clinical.v1",
                    "appointment.scheduling.v1",
                ],
                "processingMode": "batch",
                "batchSize": 1000,
                "batchTimeoutMs": 60000,
                "windowDuration": "PT5M",
            }
        ],
        "audit": [
            {
                "groupId": "audit-service-compliance",
                "topics": ["*.*.v1"],
                "processingMode": "exactly_once",
                "durabilityGuarantee": "persistent",
                "retentionPolicy": "P7Y",
                "encryptionEnabled": True,
            }
        ],
    }


def _monitoring_template() -> dict:
    return {
        "monitoring": {
            "metricsReporter": "io.confluent.monitoring.clients.interceptor.MonitoringProducerInterceptor",
            "jmxMetrics": ensure_list(
                None,
                [
                    "kafka.producer:type=producer-metrics,client-id=*",
                    "kafka.consumer:type=consumer-metrics,client-id=*",
                    "kafka.streams:type=stream-metrics,client-id=*",
                ],
            ),
            "alertRules": [
                {
                    "metric": "consumer_lag",
                    "threshold": 10000,
                    "duration": "PT5M",
                    "severity": "warning",
                },
                {
                    "metric": "error_rate",
                    "threshold": 0.05,
                    "duration": "PT2M",
                    "severity": "critical",
                },
            ],
        },
        "healthChecks": {
            "producerLatency": {
                "threshold": "PT0.1S",
                "alertChannel": "ops-team",
            },
            "consumerLag": {
                "threshold": 5000,
                "alertChannel": "dev-team",
            },
            "diskUsage": {
                "threshold": 0.8,
                "alertChannel": "infrastructure",
            },
            "replicationStatus": {
                "minInSyncReplicas": 2,
                "alertChannel": "ops-team",
            },
        },
    }


def _schema_registry_template() -> dict:
    return {
        "schemaRegistry": {
            "url": "http://schema-registry:8081",
            "compatibilityLevel": "BACKWARD",
            "subjectNaming": "TopicNameStrategy",
            "schemas": {
                "patient.lifecycle.v1-value": {
                    "version": 2,
                    "evolution": "backward_compatible",
                    "changes": [
                        "added optional field 'preferredLanguage'",
                        "added optional field 'communicationPreferences'",
                    ],
                }
            },
        }
    }


def _security_template() -> dict:
    return {
        "security": {
            "protocol": "SASL_SSL",
            "saslMechanism": "SCRAM-SHA-512",
            "sslTruststoreLocation": "/opt/kafka/ssl/truststore.jks",
            "sslKeystoreLocation": "/opt/kafka/ssl/keystore.jks",
            "encryption": {
                "inTransit": "TLS 1.3",
                "atRest": "AES-256-GCM",
            },
            "acls": [
                {
                    "principal": "User:patient-service",
                    "operations": ["Read", "Write"],
                    "topics": ["patient.lifecycle.v1"],
                },
                {
                    "principal": "User:audit-service",
                    "operations": ["Read"],
                    "topics": ["*.*.v1"],
                },
            ],
        }
    }


@api_view(["GET"])
def event_schema(request):
    """Return the base Kafka event schema used across services."""
    overrides = request.query_params.dict()
    return Response(deep_merge(_base_event_template(), overrides))


@api_view(["GET"])
def configuration(request):
    """Provide the Kafka topic, partitioning, consumer, and monitoring defaults."""
    template = {
        "topics": _topic_configuration_template(),
        "partitioning": _partitioning_strategy_template(),
        "consumerGroups": _consumer_groups_template(),
        "monitoring": _monitoring_template(),
    }
    section = request.query_params.get("section")
    if section:
        return Response(template.get(section))
    return Response(template)


@api_view(["GET"])
def governance(request):
    """Expose schema registry, retry, and security guidance."""
    retry_policy = {
        "retryPolicy": {
            "retryableExceptions": ensure_list(
                None,
                [
                    "org.apache.kafka.common.errors.TimeoutException",
                    "org.springframework.dao.TransientDataAccessException",
                    "java.net.SocketTimeoutException",
                ],
            ),
            "nonRetryableExceptions": ensure_list(
                None,
                [
                    "com.fhir.validation.ValidationException",
                    "org.springframework.security.access.AccessDeniedException",
                    "com.fhir.patient.PatientNotFoundException",
                ],
            ),
            "maxRetries": 3,
            "backoffPolicy": {
                "type": "exponential",
                "initialInterval": 1000,
                "multiplier": 2.0,
                "maxInterval": 30000,
                "randomizationFactor": 0.1,
            },
        }
    }
    template = deep_merge(_schema_registry_template(), _security_template())
    template = deep_merge(template, retry_policy)
    return Response(template)


urlpatterns = [
    path("events/schema", event_schema, name="event-schema"),
    path("config", configuration, name="configuration"),
    path("governance", governance, name="governance"),
]
