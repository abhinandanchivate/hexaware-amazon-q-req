from __future__ import annotations

from datetime import datetime

from django.db import models


class TimestampedModel(models.Model):
    """Abstract base model that tracks creation and update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HL7Message(TimestampedModel):
    message_id = models.CharField(max_length=64, unique=True)
    correlation_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32)
    raw_message = models.TextField()
    fhir_resources = models.JSONField(default=list, blank=True)
    errors = models.JSONField(default=list, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover - human-readable representation
        return f"HL7Message(message_id={self.message_id})"


class HL7BatchRequest(TimestampedModel):
    batch_id = models.CharField(max_length=64, unique=True)
    total_messages = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)
    processing_time = models.CharField(max_length=32, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"HL7BatchRequest(batch_id={self.batch_id})"


class PatientRecord(TimestampedModel):
    patient_id = models.CharField(max_length=64, unique=True)
    identifier = models.CharField(max_length=128, blank=True)
    name = models.CharField(max_length=256, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=32, blank=True)
    data = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"PatientRecord(patient_id={self.patient_id})"


class PatientMergeEvent(TimestampedModel):
    source_patient_id = models.CharField(max_length=64)
    target_patient_id = models.CharField(max_length=64)
    reason = models.TextField(blank=True)
    merge_strategy = models.CharField(max_length=64, blank=True)
    merged_fields = models.JSONField(default=list, blank=True)
    audit_reason = models.TextField(blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"PatientMergeEvent(source={self.source_patient_id}, target={self.target_patient_id})"


class PatientExportJob(TimestampedModel):
    export_id = models.CharField(max_length=64, unique=True)
    patient_id = models.CharField(max_length=64)
    status = models.CharField(max_length=32)
    format = models.CharField(max_length=16)
    include_sections = models.JSONField(default=list, blank=True)
    download_url = models.CharField(max_length=512, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"PatientExportJob(export_id={self.export_id})"


class ObservationRecord(TimestampedModel):
    observation_id = models.CharField(max_length=64, unique=True)
    patient_reference = models.CharField(max_length=128, blank=True)
    category = models.CharField(max_length=64, blank=True)
    code = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32, blank=True)
    effective_datetime = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"ObservationRecord(observation_id={self.observation_id})"


class ObservationAlertConfig(TimestampedModel):
    patient_id = models.CharField(max_length=64)
    observation_code = models.CharField(max_length=64)
    thresholds = models.JSONField(default=dict, blank=True)
    notification_channels = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("patient_id", "observation_code")

    def __str__(self) -> str:  # pragma: no cover
        return f"ObservationAlertConfig(patient={self.patient_id}, code={self.observation_code})"


class AppointmentRecord(TimestampedModel):
    appointment_id = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=32)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    patient_reference = models.CharField(max_length=128, blank=True)
    practitioner_reference = models.CharField(max_length=128, blank=True)
    service_category = models.CharField(max_length=128, blank=True)
    appointment_type = models.CharField(max_length=128, blank=True)
    data = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AppointmentRecord(appointment_id={self.appointment_id})"


class WaitlistEntry(TimestampedModel):
    appointment_id = models.CharField(max_length=64)
    patient_id = models.CharField(max_length=64)
    preferred_dates = models.JSONField(default=list, blank=True)
    preferred_times = models.JSONField(default=list, blank=True)
    priority = models.CharField(max_length=32, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"WaitlistEntry(appointment_id={self.appointment_id}, patient_id={self.patient_id})"


class AuthEvent(TimestampedModel):
    user_id = models.CharField(max_length=64)
    event_type = models.CharField(max_length=32)
    username = models.CharField(max_length=256, blank=True)
    device_info = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AuthEvent(user_id={self.user_id}, event_type={self.event_type})"


class RoleAssignmentRecord(TimestampedModel):
    assignment_id = models.CharField(max_length=64, unique=True)
    user_id = models.CharField(max_length=64)
    roles = models.JSONField(default=list, blank=True)
    permissions = models.JSONField(default=list, blank=True)
    effective_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"RoleAssignmentRecord(assignment_id={self.assignment_id})"


class AbacEvaluationRecord(TimestampedModel):
    user_id = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=64)
    action = models.CharField(max_length=32)
    decision = models.CharField(max_length=32)
    context = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AbacEvaluationRecord(user_id={self.user_id}, resource={self.resource_id})"


class TelemedicineSessionRecord(TimestampedModel):
    session_id = models.CharField(max_length=64, unique=True)
    appointment_id = models.CharField(max_length=64, blank=True)
    session_type = models.CharField(max_length=64, blank=True)
    scheduled_start = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(null=True, blank=True)
    join_urls = models.JSONField(default=dict, blank=True)
    settings = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"TelemedicineSessionRecord(session_id={self.session_id})"


class TelemedicineConsentRecord(TimestampedModel):
    session_id = models.CharField(max_length=64)
    user_id = models.CharField(max_length=64)
    consent_type = models.CharField(max_length=64)
    granted = models.BooleanField(default=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)

    class Meta:
        unique_together = ("session_id", "user_id", "consent_type")

    def __str__(self) -> str:  # pragma: no cover
        return f"TelemedicineConsentRecord(session_id={self.session_id}, user_id={self.user_id})"


class NotificationMessage(TimestampedModel):
    notification_id = models.CharField(max_length=64, unique=True)
    recipient_id = models.CharField(max_length=64)
    template = models.CharField(max_length=128, blank=True)
    channels = models.JSONField(default=list, blank=True)
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"NotificationMessage(notification_id={self.notification_id})"


class NotificationTemplate(TimestampedModel):
    name = models.CharField(max_length=128, unique=True)
    channels = models.JSONField(default=dict, blank=True)
    variables = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"NotificationTemplate(name={self.name})"


class NotificationCampaign(TimestampedModel):
    campaign_name = models.CharField(max_length=128)
    template_name = models.CharField(max_length=128)
    channels = models.JSONField(default=list, blank=True)
    recipients = models.JSONField(default=list, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"NotificationCampaign(campaign_name={self.campaign_name})"


class AnalyticsRiskScore(TimestampedModel):
    patient_id = models.CharField(max_length=64)
    risk_type = models.CharField(max_length=64)
    score = models.FloatField(default=0)
    level = models.CharField(max_length=32, blank=True)
    confidence = models.FloatField(default=0)
    factors = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("patient_id", "risk_type")

    def __str__(self) -> str:  # pragma: no cover
        return f"AnalyticsRiskScore(patient_id={self.patient_id}, risk_type={self.risk_type})"


class AnalyticsTrainingJob(TimestampedModel):
    training_job_id = models.CharField(max_length=64, unique=True)
    model_name = models.CharField(max_length=128)
    model_type = models.CharField(max_length=64)
    status = models.CharField(max_length=32)
    configuration = models.JSONField(default=dict, blank=True)
    progress = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AnalyticsTrainingJob(training_job_id={self.training_job_id})"


class AnalyticsAlertConfiguration(TimestampedModel):
    alert_id = models.CharField(max_length=64, unique=True)
    patient_id = models.CharField(max_length=64)
    model_id = models.CharField(max_length=64)
    configuration = models.JSONField(default=dict, blank=True)
    assessment = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AnalyticsAlertConfiguration(alert_id={self.alert_id})"


class AnalyticsTrendRequest(TimestampedModel):
    analysis_id = models.CharField(max_length=64, unique=True)
    parameters = models.JSONField(default=dict, blank=True)
    trends = models.JSONField(default=list, blank=True)
    correlations = models.JSONField(default=list, blank=True)
    anomalies = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AnalyticsTrendRequest(analysis_id={self.analysis_id})"


class AnalyticsFhirLinkRecord(TimestampedModel):
    linking_id = models.CharField(max_length=64, unique=True)
    patient_id = models.CharField(max_length=64)
    model_id = models.CharField(max_length=64)
    fhir_resources = models.JSONField(default=list, blank=True)
    audit_trail = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AnalyticsFhirLinkRecord(linking_id={self.linking_id})"


class AuditEventRecord(TimestampedModel):
    audit_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=64)
    user_id = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=64)
    action = models.CharField(max_length=32)
    timestamp_value = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AuditEventRecord(audit_id={self.audit_id})"


class AuditExportRecord(TimestampedModel):
    export_id = models.CharField(max_length=64, unique=True)
    parameters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32)
    download_url = models.CharField(max_length=512, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AuditExportRecord(export_id={self.export_id})"


class AuditAnomalyRecord(TimestampedModel):
    anomaly_id = models.CharField(max_length=64, unique=True)
    user_id = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=32, blank=True)
    score = models.FloatField(default=0)
    data = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"AuditAnomalyRecord(anomaly_id={self.anomaly_id})"


class FhirGatewayRequest(TimestampedModel):
    request_id = models.CharField(max_length=64, unique=True)
    resource_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=64, blank=True)
    method = models.CharField(max_length=16)
    status_code = models.PositiveIntegerField(default=200)
    response_payload = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"FhirGatewayRequest(request_id={self.request_id})"


class KafkaTopicConfiguration(TimestampedModel):
    name = models.CharField(max_length=128, unique=True)
    config = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"KafkaTopicConfiguration(name={self.name})"


class KafkaEventRecord(TimestampedModel):
    event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=128)
    payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"KafkaEventRecord(event_id={self.event_id})"


class KafkaDeadLetterRecord(TimestampedModel):
    dlq_event_id = models.CharField(max_length=64, unique=True)
    original_event = models.JSONField(default=dict, blank=True)
    failure_info = models.JSONField(default=dict, blank=True)
    routing = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"KafkaDeadLetterRecord(dlq_event_id={self.dlq_event_id})"


# Utility helpers -----------------------------------------------------------

def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
