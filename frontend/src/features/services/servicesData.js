
const servicesData = [
  {
    key: 'hl7-parser',
    name: 'HL7 Parser Service',
    baseUrl: '/api/v1/hl7-parser',
    description: 'Transforms HL7 v2 messages into FHIR resources with validation and Kafka fan-out.',
    endpoints: [
      {
        id: 'hl7-ingest',
        name: 'HL7 Message Ingestion',
        method: 'POST',
        path: '/ingest',
        summary: 'Accepts an HL7 ADT message and returns correlated FHIR resources.',
        requestHeaders: [
          { key: 'Content-Type', value: 'application/hl7-v2' },
          { key: 'Authorization', value: 'Bearer {jwt_token}' }
        ],
        requestPayload: `MSH|^~\\&|SENDING_APP|SENDING_FACILITY|RECEIVING_APP|RECEIVING_FACILITY|20230901123045||ADT^A0\nEVN||20230901123045|||USER123\nPID|||MRN12345||Doe^John^M||19800115|M|||123 Main St^^City^ST^12345^USA||5551234567|\nPV1||I|ICU^101^A|||DOC123^Smith^Jane^MD|||SUR||||A|||DOC123|INS|12345|||||||||||||||||||20230901123045`,
        responsePayload: `{
  "messageId": "MSG001",
  "correlationId": "corr-uuid-123",
  "status": "processed",
  "timestamp": "2023-09-01T12:30:45Z",
  "fhirResources": [
    {
      "resourceType": "Patient",
      "id": "patient-12345",
      "identifier": [{ "value": "MRN12345" }],
      "name": [{ "family": "Doe", "given": ["John"] }]
    }
  ],
  "errors": []
}`,
        validationRules: [
          'MSH segment must be present',
          'Message Control ID must be unique',
          'Sending/Receiving applications must be registered',
          'HL7 version must be 2.3–2.8'
        ],
        kafkaEvents: ['hl7.message.received', 'fhir.resource.created']
      },
      {
        id: 'hl7-parse-status',
        name: 'Message Parsing Status',
        method: 'GET',
        path: '/parse-status/{messageId}',
        summary: 'Retrieves the processing progress for a specific HL7 message.',
        responsePayload: `{
  "messageId": "MSG001",
  "status": "completed",
  "processedAt": "2023-09-01T12:30:45Z",
  "resourcesCreated": 3,
  "errors": []
}`,
        validationRules: ['Message must exist', 'Caller must have access to audit trail']
      },
      {
        id: 'hl7-batch',
        name: 'Batch Processing',
        method: 'POST',
        path: '/batch',
        summary: 'Submit a batch of HL7 messages for prioritised processing.',
        requestPayload: `{
  "batchId": "batch-001",
  "messages": [
    {
      "messageId": "MSG001",
      "content": "MSH|^~\\&|...",
      "priority": "normal"
    }
  ]
}`,
        responsePayload: `{
  "batchId": "batch-001",
  "totalMessages": 10,
  "processed": 8,
  "failed": 2,
  "processingTime": "45.2s",
  "status": "partial_success"
}`
      }
    ]
  },
  {
    key: 'patients',
    name: 'Patient Service',
    baseUrl: '/api/v1/patients',
    description: 'Manages patient demographics, merges, exports and search.',
    endpoints: [
      {
        id: 'patient-registration',
        name: 'Patient Registration',
        method: 'POST',
        path: '/',
        summary: 'Registers a patient using a FHIR Patient resource.',
        requestHeaders: [
          { key: 'Content-Type', value: 'application/fhir+json' },
          { key: 'Authorization', value: 'Bearer {jwt_token}' }
        ],
        requestPayload: `{
  "resourceType": "Patient",
  "identifier": [
    {
      "use": "usual",
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
            "code": "MR"
          }
        ]
      },
      "value": "MRN12345"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Doe",
      "given": ["John", "Michael"]
    }
  ],
  "gender": "male",
  "birthDate": "1980-01-15",
  "address": [
    {
      "use": "home",
      "line": ["123 Main St"],
      "city": "Springfield",
      "state": "IL",
      "postalCode": "62701",
      "country": "US"
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "555-123-4567",
      "use": "mobile"
    },
    {
      "system": "email",
      "value": "john.doe@email.com"
    }
  ]
}`,
        responsePayload: `{
  "resourceType": "Patient",
  "id": "patient-uuid-123",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2023-09-01T12:30:45Z"
  },
  "identifier": [
    {
      "use": "usual",
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
            "code": "MR"
          }
        ]
      },
      "value": "MRN12345"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Doe",
      "given": ["John", "Michael"]
    }
  ],
  "gender": "male",
  "birthDate": "1980-01-15"
}`,
        validationRules: [
          'At least one identifier required',
          'Valid email format if provided',
          'Phone number format validation',
          'Birth date cannot be in the future',
          'Gender must be from ValueSet',
          'Required fields: name, gender, birthDate'
        ],
        kafkaEvents: ['patient.registered', 'audit.patient.created']
      },
      {
        id: 'patient-update',
        name: 'Patient Profile Update',
        method: 'PUT',
        path: '/{patientId}',
        summary: 'Updates an existing patient record with auditing.',
        validationRules: ['Patient must exist', 'User must have permission to update', 'Audit trail required for all changes']
      },
      {
        id: 'patient-search',
        name: 'Patient Search',
        method: 'GET',
        path: '/search',
        summary: 'Searches for patients using demographic criteria.',
        queryParameters: ['identifier', 'name', 'birthdate', 'phone', 'email', '_fuzzy'],
        responsePayload: `{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 1,
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "id": "patient-uuid-123",
        "name": [{ "family": "Doe", "given": ["John"] }]
      }
    }
  ]
}`
      },
      {
        id: 'patient-merge',
        name: 'Patient Record Merge',
        method: 'POST',
        path: '/{sourceId}/merge/{targetId}',
        summary: 'Consolidates duplicate patient records with audit capture.',
        requestPayload: `{
  "reason": "Duplicate records identified",
  "mergeStrategy": "keep_latest",
  "fields": ["contact", "address"],
  "auditReason": "Data quality improvement"
}`,
        responsePayload: `{
  "status": "merged",
  "resultPatientId": "patient-uuid-123",
  "mergedFields": ["telecom", "address"],
  "auditId": "audit-uuid-456"
}`
      },
      {
        id: 'patient-export',
        name: 'Data Export',
        method: 'GET',
        path: '/{patientId}/export',
        summary: 'Exports longitudinal patient data in multiple formats.',
        queryParameters: ['format=pdf|fhir|cda', 'includeSections=demographics,vitals,labs,medications'],
        responsePayload: `{
  "exportId": "export-uuid-789",
  "status": "completed",
  "downloadUrl": "/api/v1/exports/export-uuid-789/download",
  "format": "pdf",
  "size": "2.4MB",
  "expiresAt": "2023-09-08T12:30:45Z"
}`
      }
    ]
  },
  {
    key: 'observations',
    name: 'Observation Service',
    baseUrl: '/api/v1/observations',
    description: 'Captures vitals, labs, and analytics-ready observation trends.',
    endpoints: [
      {
        id: 'observation-vital-signs',
        name: 'Vital Signs Entry',
        method: 'POST',
        path: '/',
        summary: 'Records a vital sign observation with UCUM-compliant units.',
        requestPayload: `{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "85354-9",
        "display": "Blood pressure panel with all children optional"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-uuid-123"
  },
  "effectiveDateTime": "2023-09-01T12:30:45Z",
  "component": [
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
          }
        ]
      },
      "valueQuantity": {
        "value": 120,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    }
  ]
}`,
        responsePayload: `{
  "resourceType": "Observation",
  "id": "obs-uuid-123",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2023-09-01T12:30:45Z"
  },
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs"
        }
      ]
    }
  ]
}`,
        validationRules: [
          'LOINC codes must be valid',
          'Units must be UCUM compliant',
          'Vital sign ranges validation',
          'Patient reference must exist',
          'Effective date cannot be in future'
        ],
        kafkaEvents: ['observation.created', 'alert.triggered', 'trend.calculated']
      },
      {
        id: 'observation-lab-results',
        name: 'Lab Results Integration',
        method: 'POST',
        path: '/lab-results',
        summary: 'Bundles laboratory observations in a transaction.',
        requestPayload: `{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "request": {
        "method": "POST",
        "url": "Observation"
      },
      "resource": {
        "resourceType": "Observation",
        "status": "final",
        "category": [
          {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory"
              }
            ]
          }
        ],
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "2339-0",
              "display": "Glucose"
            }
          ]
        },
        "valueQuantity": {
          "value": 95,
          "unit": "mg/dL",
          "system": "http://unitsofmeasure.org"
        }
      }
    }
  ]
}`
      },
      {
        id: 'observation-trends',
        name: 'Trend Visualization Data',
        method: 'GET',
        path: '/{patientId}/trends',
        summary: 'Calculates longitudinal trend data for a given patient and metric.',
        queryParameters: ['code', 'category', 'period'],
        responsePayload: `{
  "patientId": "patient-uuid-123",
  "observationType": "glucose",
  "unit": "mg/dL",
  "timeRange": {
    "start": "2023-08-01T00:00:00Z",
    "end": "2023-09-01T00:00:00Z"
  },
  "dataPoints": [
    { "timestamp": "2023-08-01T08:00:00Z", "value": 95, "status": "normal" },
    { "timestamp": "2023-08-15T08:00:00Z", "value": 110, "status": "high" }
  ],
  "referenceRanges": {
    "low": 70,
    "high": 100
  }
}`
      },
      {
        id: 'observation-alerts',
        name: 'Clinical Alerts',
        method: 'POST',
        path: '/alerts/configure',
        summary: 'Configures personalised notification thresholds for observations.',
        requestPayload: `{
  "patientId": "patient-uuid-123",
  "observationCode": "8480-6",
  "thresholds": {
    "critical": {
      "high": 180,
      "low": 90
    },
    "warning": {
      "high": 140,
      "low": 100
    }
  },
  "notificationChannels": ["email", "sms", "app"],
  "active": true
}`,
        kafkaEvents: ['observation.created', 'alert.triggered', 'trend.calculated']
      }
    ]
  },
  {
    key: 'appointments',
    name: 'Appointment Service',
    baseUrl: '/api/v1/appointments',
    description: 'Handles booking, availability, and waitlist orchestration.',
    endpoints: [
      {
        id: 'appointment-booking',
        name: 'Appointment Booking',
        method: 'POST',
        path: '/',
        summary: 'Schedules a practitioner appointment with confirmation metadata.',
        requestPayload: `{
  "resourceType": "Appointment",
  "status": "booked",
  "serviceCategory": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/service-category",
          "code": "17",
          "display": "General Practice"
        }
      ]
    }
  ],
  "appointmentType": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
        "code": "ROUTINE"
      }
    ]
  },
  "start": "2023-09-15T09:00:00Z",
  "end": "2023-09-15T09:30:00Z",
  "participant": [
    {
      "actor": {
        "reference": "Patient/patient-uuid-123"
      },
      "required": "required",
      "status": "accepted"
    },
    {
      "actor": {
        "reference": "Practitioner/doc-uuid-456"
      },
      "required": "required",
      "status": "accepted"
    }
  ]
}`,
        responsePayload: `{
  "resourceType": "Appointment",
  "id": "appt-uuid-789",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2023-09-01T12:30:45Z"
  },
  "status": "booked",
  "start": "2023-09-15T09:00:00Z",
  "end": "2023-09-15T09:30:00Z",
  "confirmationCode": "CONF123456"
}`,
        validationRules: [
          'Start time must be in future',
          'End time must be after start time',
          'Practitioner must be available',
          'Patient cannot have overlapping appointments',
          'Business hours validation'
        ],
        kafkaEvents: ['appointment.booked', 'appointment.cancelled', 'waitlist.added']
      },
      {
        id: 'appointment-availability',
        name: 'Real-time Availability',
        method: 'GET',
        path: '/availability',
        summary: 'Displays open appointment slots for a practitioner.',
        queryParameters: ['practitioner', 'date', 'duration', 'serviceType'],
        responsePayload: `{
  "date": "2023-09-15",
  "practitioner": "doc-uuid-456",
  "availableSlots": [
    { "start": "2023-09-15T09:00:00Z", "end": "2023-09-15T09:30:00Z", "type": "available" },
    { "start": "2023-09-15T10:00:00Z", "end": "2023-09-15T10:30:00Z", "type": "tentative" }
  ]
}`
      },
      {
        id: 'appointment-waitlist',
        name: 'Waitlist Management',
        method: 'POST',
        path: '/{appointmentId}/waitlist',
        summary: 'Registers a patient for waitlist notifications.',
        requestPayload: `{
  "patientId": "patient-uuid-123",
  "preferredDates": ["2023-09-15", "2023-09-16"],
  "preferredTimes": ["morning", "afternoon"],
  "priority": "routine",
  "notificationPreferences": {
    "email": true,
    "sms": true,
    "advanceNotice": "24h"
  }
}`
      }
    ]
  },
  {
    key: 'auth',
    name: 'User Auth Service',
    baseUrl: '/api/v1/auth',
    description: 'Handles login, registration, password resets, and MFA.',
    endpoints: [
      {
        id: 'auth-login',
        name: 'User Login',
        method: 'POST',
        path: '/login',
        summary: 'Authenticates a user with MFA and device metadata.',
        requestPayload: `{
  "username": "john.doe@example.com",
  "password": "SecurePass123!",
  "mfaCode": "123456",
  "deviceInfo": {
    "deviceId": "device-uuid-123",
    "userAgent": "Mozilla/5.0...",
    "ipAddress": "192.168.1.100"
  }
}`,
        responsePayload: `{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "refresh-token-uuid",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": {
    "id": "user-uuid-123",
    "email": "john.doe@example.com",
    "roles": ["patient"],
    "permissions": ["read:own_records", "write:own_profile"]
  }
}`,
        validationRules: [
          'Email format validation',
          'Password complexity requirements',
          'Rate limiting: 5 attempts per 15 minutes',
          'MFA required for privileged accounts',
          'Device registration for new devices'
        ],
        kafkaEvents: ['user.authenticated', 'security.failed_login']
      },
      {
        id: 'auth-register',
        name: 'User Registration',
        method: 'POST',
        path: '/register',
        summary: 'Registers a new patient portal user with verification.',
        requestPayload: `{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "confirmPassword": "SecurePass123!",
  "profile": {
    "firstName": "John",
    "lastName": "Doe",
    "phone": "555-123-4567",
    "dateOfBirth": "1980-01-15"
  },
  "acceptTerms": true,
  "verificationMethod": "email"
}`
      },
      {
        id: 'auth-password-reset',
        name: 'Password Reset',
        method: 'POST',
        path: '/password-reset',
        summary: 'Initiates a password reset workflow.',
        requestPayload: `{
  "email": "john.doe@example.com",
  "resetMethod": "email"
}`,
        responsePayload: `{
  "status": "sent",
  "message": "Password reset instructions sent to email",
  "resetTokenId": "reset-uuid-123",
  "expiresIn": 3600
}`
      },
      {
        id: 'auth-mfa',
        name: 'Multi-Factor Authentication Setup',
        method: 'POST',
        path: '/mfa/setup',
        summary: 'Configures TOTP MFA devices for a user.',
        requestPayload: `{
  "method": "totp",
  "deviceName": "iPhone 12"
}`,
        responsePayload: `{
  "qrCode": "data:image/png;base64,iVBOR...",
  "secret": "JBSWY3DPEHPK3PXP",
  "backupCodes": ["12345678", "87654321"]
}`,
        kafkaEvents: ['user.registered', 'user.authenticated']
      }
    ]
  },
  {
    key: 'roles',
    name: 'Role Management Service',
    baseUrl: '/api/v1/roles',
    description: 'Manages RBAC/ABAC assignments and permission evaluations.',
    endpoints: [
      {
        id: 'roles-assign',
        name: 'Role Assignment',
        method: 'POST',
        path: '/assign',
        summary: 'Assigns one or more roles to a user with temporal bounds.',
        requestPayload: `{
  "userId": "user-uuid-123",
  "roles": ["doctor", "department_head"],
  "effectiveDate": "2023-09-01T00:00:00Z",
  "expiryDate": "2024-09-01T00:00:00Z",
  "assignedBy": "admin-uuid-456",
  "reason": "Promotion to department head"
}`,
        responsePayload: `{
  "assignmentId": "assignment-uuid-789",
  "status": "active",
  "permissions": [
    "read:patient_records",
    "write:observations",
    "manage:department_users"
  ],
  "effectiveDate": "2023-09-01T00:00:00Z"
}`
      },
      {
        id: 'roles-validate',
        name: 'Permission Validation',
        method: 'POST',
        path: '/validate',
        summary: 'Evaluates a user's permission for a specific resource action.',
        requestPayload: `{
  "userId": "user-uuid-123",
  "resource": "Patient/patient-uuid-456",
  "action": "read",
  "context": {
    "facility": "facility-uuid-789",
    "department": "cardiology"
  }
}`,
        responsePayload: `{
  "allowed": true,
  "decision": "permit",
  "reason": "User has doctor role with read permission",
  "conditions": ["audit_required", "time_limited"]
}`
      },
      {
        id: 'roles-abac',
        name: 'Attribute-Based Access Control',
        method: 'POST',
        path: '/abac/evaluate',
        summary: 'Evaluates fine-grained ABAC policies for a subject and resource.',
        requestPayload: `{
  "subject": {
    "userId": "user-uuid-123",
    "roles": ["doctor"],
    "department": "cardiology",
    "facility": "facility-uuid-789"
  },
  "resource": {
    "type": "Patient",
    "id": "patient-uuid-456",
    "attributes": {
      "facility": "facility-uuid-789",
      "department": "cardiology"
    }
  },
  "action": "read",
  "environment": {
    "time": "2023-09-01T14:30:00Z",
    "location": "clinic"
  }
}`,
        kafkaEvents: ['role.assigned', 'permission.denied', 'access.granted']
      }
    ]
  },
  {
    key: 'telemedicine',
    name: 'Telemedicine Service',
    baseUrl: '/api/v1/telemedicine',
    description: 'Coordinates virtual visit sessions and consent tracking.',
    endpoints: [
      {
        id: 'telemedicine-session',
        name: 'Session Creation',
        method: 'POST',
        path: '/sessions',
        summary: 'Creates a secure telemedicine session and join URLs.',
        requestPayload: `{
  "appointmentId": "appt-uuid-789",
  "participants": [
    { "userId": "patient-uuid-123", "role": "patient" },
    { "userId": "doc-uuid-456", "role": "provider" }
  ],
  "sessionType": "video_consultation",
  "scheduledStart": "2023-09-15T09:00:00Z",
  "estimatedDuration": 30
}`,
        responsePayload: `{
  "sessionId": "session-uuid-101",
  "joinUrls": {
    "patient": "https://telemedicine.example.com/join/patient-token-123",
    "provider": "https://telemedicine.example.com/join/provider-token-456"
  },
  "accessWindow": {
    "start": "2023-09-15T08:50:00Z",
    "end": "2023-09-15T09:40:00Z"
  },
  "sessionSettings": {
    "recordingEnabled": false,
    "chatEnabled": true,
    "screenShareEnabled": true
  }
}`,
        kafkaEvents: ['session.started', 'session.ended']
      },
      {
        id: 'telemedicine-consent',
        name: 'Consent Management',
        method: 'POST',
        path: '/consent',
        summary: 'Captures explicit consent for telemedicine features.',
        requestPayload: `{
  "sessionId": "session-uuid-101",
  "userId": "patient-uuid-123",
  "consentType": "video_recording",
  "granted": true,
  "timestamp": "2023-09-15T08:55:00Z",
  "ipAddress": "192.168.1.100"
}`,
        kafkaEvents: ['consent.recorded']
      },
      {
        id: 'telemedicine-metrics',
        name: 'Quality Monitoring',
        method: 'GET',
        path: '/sessions/{sessionId}/metrics',
        summary: 'Reports call quality metrics for compliance review.',
        responsePayload: `{
  "sessionId": "session-uuid-101",
  "qualityMetrics": {
    "averageLatency": 45,
    "packetLoss": 0.2,
    "videoQuality": "HD",
    "audioQuality": "excellent"
  },
  "duration": 1800,
  "participants": [
    {
      "userId": "patient-uuid-123",
      "connectionTime": 1795,
      "disconnections": 0
    }
  ]
}`
      }
    ]
  },
  {
    key: 'notifications',
    name: 'Notification Service',
    baseUrl: '/api/v1/notifications',
    description: 'Manages multichannel notifications and templates.',
    endpoints: [
      {
        id: 'notifications-send',
        name: 'Send Notification',
        method: 'POST',
        path: '/send',
        summary: 'Queues notifications across multiple channels.',
        requestPayload: `{
  "recipientId": "user-uuid-123",
  "channels": ["email", "sms"],
  "template": "appointment_reminder",
  "data": {
    "appointmentDate": "2023-09-15T09:00:00Z",
    "doctorName": "Dr. Jane Smith",
    "location": "Room 101, Main Building"
  },
  "scheduledAt": "2023-09-14T20:00:00Z",
  "priority": "normal"
}`,
        responsePayload: `{
  "notificationId": "notif-uuid-123",
  "status": "scheduled",
  "channels": [
    { "type": "email", "status": "queued", "estimatedDelivery": "2023-09-14T20:00:30Z" },
    { "type": "sms", "status": "queued", "estimatedDelivery": "2023-09-14T20:00:15Z" }
  ]
}`,
        kafkaEvents: ['notification.sent', 'notification.failed', 'notification.delivered']
      },
      {
        id: 'notifications-template',
        name: 'Template Management',
        method: 'POST',
        path: '/templates',
        summary: 'Creates or updates reusable notification templates.',
        requestPayload: `{
  "name": "appointment_reminder",
  "channels": {
    "email": {
      "subject": "Appointment Reminder - {{appointmentDate}}",
      "body": "Dear {{patientName}}, you have an appointment with {{doctorName}} on {{appointmentDate}}."
    },
    "sms": {
      "body": "Reminder: Appointment with {{doctorName}} on {{appointmentDate}}. Reply STOP to opt out."
    }
  },
  "variables": ["patientName", "doctorName", "appointmentDate"]
}`
      },
      {
        id: 'notifications-bulk',
        name: 'Bulk Notification',
        method: 'POST',
        path: '/bulk',
        summary: 'Launches a campaign to multiple recipients.',
        requestPayload: `{
  "campaignName": "flu_shot_reminder",
  "template": "vaccination_reminder",
  "recipients": [
    { "userId": "user-uuid-123", "data": { "patientName": "John Doe" } },
    { "userId": "user-uuid-456", "data": { "patientName": "Jane Smith" } }
  ],
  "channels": ["email"],
  "scheduledAt": "2023-09-20T10:00:00Z"
}`
      }
    ]
  },
  {
    key: 'analytics',
    name: 'Analytics Service',
    baseUrl: '/api/v1/analytics',
    description: 'Provides risk scoring, ML lifecycle, and operational insights.',
    endpoints: [
      {
        id: 'analytics-risk-score',
        name: 'Risk Scoring',
        method: 'POST',
        path: '/risk-score',
        summary: 'Calculates condition-specific risk for a patient.',
        requestPayload: `{
  "patientId": "patient-uuid-123",
  "riskType": "diabetes",
  "factors": [
    { "type": "observation", "code": "33747-0", "value": 95, "unit": "mg/dL" },
    { "type": "demographic", "age": 43, "gender": "male", "bmi": 28.5 }
  ]
}`,
        responsePayload: `{
  "patientId": "patient-uuid-123",
  "riskType": "diabetes",
  "score": 0.75,
  "level": "high",
  "confidence": 0.89,
  "factors": [
    { "name": "BMI", "contribution": 0.35, "weight": "high" },
    { "name": "Family History", "contribution": 0.25, "weight": "medium" }
  ],
  "recommendations": [
    "Regular glucose monitoring",
    "Dietary consultation"
  ],
  "calculatedAt": "2023-09-01T12:30:45Z"
}`,
        validationRules: [
          'Minimum dataset size: 1000 records',
          'Feature correlation analysis required',
          'Data quality validation mandatory',
          'Privacy compliance verification',
          'Model interpretability assessment'
        ],
        kafkaEvents: ['risk.calculated']
      },
      {
        id: 'analytics-ml-train',
        name: 'ML Model Training Pipeline',
        method: 'POST',
        path: '/ml/models/train',
        summary: 'Configures and starts a machine learning training job.',
        requestPayload: `{
  "trainingJob": {
    "modelName": "diabetes_risk_classifier",
    "modelType": "classification",
    "algorithm": "random_forest",
    "targetVariable": "diabetes_diagnosis",
    "features": [
      {
        "name": "age",
        "type": "numeric",
        "source": "Patient.birthDate",
        "preprocessing": "age_calculation"
      },
      {
        "name": "bmi",
        "type": "numeric",
        "source": "Observation",
        "loincCode": "39156-5",
        "preprocessing": "outlier_removal"
      },
      {
        "name": "glucose_level",
        "type": "numeric",
        "source": "Observation",
        "loincCode": "2339-0",
        "aggregation": "latest_value"
      },
      {
        "name": "family_history",
        "type": "categorical",
        "source": "FamilyMemberHistory",
        "valueSet": "diabetes_conditions"
      }
    ],
    "trainingParameters": {
      "dataRange": {
        "start": "2020-01-01",
        "end": "2023-08-31"
      },
      "validationSplit": 0.2,
      "testSplit": 0.1,
      "hyperparameters": {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
        "random_state": 42
      },
      "crossValidation": {
        "folds": 5,
        "stratified": true
      }
    },
    "dataPrivacy": {
      "anonymization": "k_anonymity",
      "k_value": 5,
      "excludePII": true,
      "auditRequired": true
    }
  }
}`,
        responsePayload: `{
  "trainingJobId": "job-uuid-123",
  "status": "running",
  "estimatedCompletion": "2023-09-01T14:30:45Z",
  "datasetInfo": {
    "totalRecords": 15420,
    "trainingRecords": 12336,
    "validationRecords": 1542,
    "testRecords": 1542,
    "featureCount": 15,
    "classDistribution": {
      "diabetes": 0.23,
      "pre_diabetes": 0.31,
      "normal": 0.46
    }
  },
  "progress": {
    "currentStep": "feature_engineering",
    "completionPercent": 25,
    "estimatedTimeRemaining": "PT45M"
  }
}`,
        validationRules: [
          'Minimum dataset size: 1000 records',
          'Feature correlation analysis required',
          'Data quality validation mandatory',
          'Privacy compliance verification',
          'Model interpretability assessment'
        ],
        kafkaEvents: ['model.trained']
      },
      {
        id: 'analytics-ml-alerts',
        name: 'Personalized Clinical Alerts',
        method: 'POST',
        path: '/ml/alerts/personalized',
        summary: 'Creates AI-driven alert configurations with contextual factors.',
        requestPayload: `{
  "patientId": "patient-uuid-123",
  "modelId": "model-uuid-456",
  "alertConfiguration": {
    "riskThreshold": 0.75,
    "alertTypes": ["high_risk", "trend_deterioration"],
    "timeHorizon": "P30D",
    "updateFrequency": "daily"
  },
  "contextualFactors": [
    {
      "type": "recent_observations",
      "lookbackPeriod": "P7D",
      "weight": 0.4
    },
    {
      "type": "medication_adherence",
      "source": "MedicationStatement",
      "weight": 0.3
    },
    {
      "type": "lifestyle_factors",
      "source": "Observation",
      "categories": ["exercise", "diet", "smoking"],
      "weight": 0.3
    }
  ]
}`,
        responsePayload: `{
  "alertId": "alert-uuid-789",
  "patientId": "patient-uuid-123",
  "riskAssessment": {
    "overallRisk": 0.82,
    "riskLevel": "high",
    "confidence": 0.89,
    "prediction": {
      "condition": "type_2_diabetes",
      "probability": 0.82,
      "timeHorizon": "P30D"
    }
  },
  "contributingFactors": [
    {
      "factor": "elevated_glucose",
      "impact": 0.35,
      "recentTrend": "increasing",
      "lastValue": 145,
      "referenceRange": "70-100 mg/dL"
    },
    {
      "factor": "bmi",
      "impact": 0.28,
      "value": 32.5,
      "category": "obese"
    }
  ],
  "recommendations": [
    {
      "type": "clinical_action",
      "priority": "high",
      "action": "Schedule endocrinology consultation",
      "reasoning": "High diabetes risk with recent glucose elevation"
    },
    {
      "type": "lifestyle_intervention",
      "priority": "medium",
      "action": "Initiate dietary counseling",
      "evidenceLevel": "strong"
    }
  ],
  "fhirResources": [
    {
      "resourceType": "RiskAssessment",
      "id": "risk-assess-uuid-101",
      "status": "final"
    }
  ]
}`,
        kafkaEvents: ['alert.generated']
      },
      {
        id: 'analytics-model-version',
        name: 'Model Versioning and Lifecycle',
        method: 'POST',
        path: '/ml/models/{modelId}/versions',
        summary: 'Publishes a new model version with deployment metadata.',
        requestPayload: `{
  "versionInfo": {
    "version": "2.1.0",
    "description": "Improved diabetes risk model with additional lifestyle factors",
    "trainingJobId": "job-uuid-123",
    "baselineModel": "model-uuid-456-v2.0.0"
  },
  "performanceMetrics": {
    "accuracy": 0.89,
    "precision": 0.87,
    "recall": 0.91,
    "f1Score": 0.89,
    "auc": 0.94,
    "crossValidationScore": 0.88
  },
  "modelArtifacts": {
    "modelFile": "diabetes_rf_v2.1.0.pkl",
    "featureImportance": "feature_importance_v2.1.0.json",
    "preprocessor": "preprocessor_v2.1.0.pkl",
    "metadata": "model_metadata_v2.1.0.json"
  },
  "deploymentConfig": {
    "environment": "production",
    "rolloutStrategy": "blue_green",
    "canaryPercentage": 10,
    "monitoringPeriod": "P7D"
  }
}`,
        responsePayload: `{
  "modelVersionId": "model-version-uuid-456",
  "status": "deployed",
  "deploymentTimestamp": "2023-09-01T12:30:45Z",
  "performanceComparison": {
    "previousVersion": {
      "version": "2.0.0",
      "accuracy": 0.85,
      "auc": 0.91
    },
    "improvement": {
      "accuracy": 0.04,
      "auc": 0.03,
      "statisticalSignificance": true
    }
  },
  "productionMetrics": {
    "predictionLatency": "PT0.05S",
    "throughput": "1000/minute",
    "errorRate": 0.001
  }
}`
      },
      {
        id: 'analytics-trends',
        name: 'Healthcare Trend Analysis',
        method: 'GET',
        path: '/analytics/trends',
        summary: 'Generates longitudinal KPI dashboards with demographic breakdowns.',
        queryParameters: ['metric', 'timeRange', 'granularity', 'demographics', 'facility'],
        responsePayload: `{
  "analysisId": "trend-analysis-uuid-789",
  "timeRange": {
    "start": "2022-09-01T00:00:00Z",
    "end": "2023-09-01T00:00:00Z"
  },
  "trends": [
    {
      "metric": "readmission_rate",
      "overall": {
        "currentValue": 0.12,
        "previousPeriod": 0.15,
        "changePercent": -20.0,
        "trend": "decreasing",
        "significance": "p < 0.05"
      },
      "byDemographics": [
        { "segment": "age_65_plus", "value": 0.18, "trend": "stable", "sampleSize": 1247 },
        { "segment": "cardiology_dept", "value": 0.08, "trend": "decreasing", "sampleSize": 892 }
      ],
      "timeSeriesData": [
        { "period": "2022-09", "value": 0.15, "confidenceInterval": [0.13, 0.17] },
        { "period": "2023-08", "value": 0.12, "confidenceInterval": [0.10, 0.14] }
      ]
    }
  ],
  "correlations": [
    {
      "metric1": "readmission_rate",
      "metric2": "average_length_of_stay",
      "correlation": -0.65,
      "significance": "p < 0.001"
    }
  ],
  "anomalies": [
    {
      "metric": "infection_rate",
      "period": "2023-06",
      "value": 0.08,
      "expected": 0.05,
      "zScore": 2.3,
      "investigation": "required"
    }
  ]
}`
      },
      {
        id: 'analytics-link-fhir',
        name: 'FHIR Resource Linking for Predictions',
        method: 'POST',
        path: '/ml/predictions/link-fhir',
        summary: 'Anchors ML predictions to canonical FHIR resources.',
        requestPayload: `{
  "predictionId": "prediction-uuid-123",
  "patientId": "patient-uuid-456",
  "modelId": "model-uuid-789",
  "fhirMapping": {
    "primaryResource": {
      "resourceType": "RiskAssessment",
      "method": {
        "coding": [
          {
            "system": "http://example.org/ml-models",
            "code": "diabetes_risk_rf_v2.1.0",
            "display": "Diabetes Risk Random Forest v2.1.0"
          }
        ]
      },
      "prediction": [
        {
          "outcome": {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "44054006",
                "display": "Type 2 diabetes mellitus"
              }
            ]
          },
          "probabilityDecimal": 0.82,
          "whenRange": {
            "low": { "value": 30, "unit": "d" },
            "high": { "value": 90, "unit": "d" }
          }
        }
      ],
      "supportingResources": [
        {
          "resourceType": "DetectedIssue",
          "status": "final",
          "category": {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "CAUTION"
              }
            ]
          },
          "detail": "High risk for developing diabetes based on current health indicators"
        }
      ]
    }
  }
}`,
        responsePayload: `{
  "linkingId": "fhir-link-uuid-101",
  "fhirResources": [
    {
      "resourceType": "RiskAssessment",
      "id": "risk-assess-uuid-202",
      "status": "final",
      "subject": { "reference": "Patient/patient-uuid-456" },
      "performer": { "reference": "Device/ml-model-device-uuid-303" },
      "prediction": [
        {
          "outcome": {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "44054006",
                "display": "Type 2 diabetes mellitus"
              }
            ]
          },
          "probabilityDecimal": 0.82
        }
      ]
    }
  ],
  "auditTrail": {
    "createdBy": "ml-system",
    "createdAt": "2023-09-01T12:30:45Z",
    "modelVersion": "2.1.0",
    "inputFeatures": 15,
    "confidence": 0.89
  }
}`
      }
    ]
  },
  {
    key: 'audit',
    name: 'Audit Logging Service',
    baseUrl: '/api/v1/audit',
    description: 'Captures immutable audit events, exports, and anomaly detection.',
    endpoints: [
      {
        id: 'audit-log-event',
        name: 'Log Access Event',
        method: 'POST',
        path: '/events',
        summary: 'Writes a tamper-evident access log entry.',
        requestPayload: `{
  "eventType": "data_access",
  "userId": "user-uuid-123",
  "resourceType": "Patient",
  "resourceId": "patient-uuid-456",
  "action": "read",
  "timestamp": "2023-09-01T12:30:45Z",
  "sessionId": "session-uuid-789",
  "ipAddress": "192.168.1.100",
  "userAgent": "Mozilla/5.0...",
  "metadata": {
    "reason": "Patient consultation",
    "department": "cardiology",
    "facility": "facility-uuid-001"
  }
}`,
        responsePayload: `{
  "auditId": "audit-uuid-123",
  "status": "logged",
  "timestamp": "2023-09-01T12:30:45Z",
  "immutableHash": "sha256:abc123def456..."
}`,
        kafkaEvents: ['audit.logged', 'audit.anomaly_detected']
      },
      {
        id: 'audit-export',
        name: 'Export Audit Logs',
        method: 'GET',
        path: '/export',
        summary: 'Exports audit trail data for compliance review.',
        queryParameters: ['startDate', 'endDate', 'userId', 'resourceType', 'format'],
        responsePayload: `{
  "exportId": "export-uuid-456",
  "status": "processing",
  "format": "csv",
  "downloadUrl": "/api/v1/audit/exports/export-uuid-456",
  "estimatedCompletion": "2023-09-01T12:35:45Z",
  "digitalSignature": "MIIC..."
}`
      },
      {
        id: 'audit-anomalies',
        name: 'Anomaly Detection',
        method: 'GET',
        path: '/anomalies',
        summary: 'Highlights anomalous access behaviour over a recent window.',
        responsePayload: `{
  "period": "P7D",
  "anomalies": [
    {
      "type": "unusual_access_pattern",
      "userId": "user-uuid-123",
      "description": "Access to 50+ patient records in 1 hour",
      "severity": "medium",
      "timestamp": "2023-09-01T02:00:00Z",
      "score": 0.75
    }
  ]
}`
      }
    ]
  },
  {
    key: 'fhir-gateway',
    name: 'FHIR API Gateway',
    baseUrl: '/fhir/R4',
    description: 'Externalised SMART-on-FHIR gateway and metadata endpoints.',
    endpoints: [
      {
        id: 'fhir-patient',
        name: 'External FHIR Access',
        method: 'GET',
        path: '/Patient/{patientId}',
        summary: 'Reads a patient resource from the external FHIR facade.',
        requestHeaders: [{ key: 'Authorization', value: 'Bearer {api_key}' }, { key: 'Accept', value: 'application/fhir+json' }],
        responsePayload: `{
  "resourceType": "Patient",
  "id": "patient-uuid-123",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2023-09-01T12:30:45Z"
  },
  "identifier": [
    {
      "use": "usual",
      "value": "MRN12345"
    }
  ]
}`
      },
      {
        id: 'fhir-metadata',
        name: 'Capability Statement',
        method: 'GET',
        path: '/metadata',
        summary: 'Returns the capability statement for the gateway.',
        responsePayload: `{
  "resourceType": "CapabilityStatement",
  "status": "active",
  "date": "2023-09-01",
  "publisher": "Healthcare Organization",
  "kind": "instance",
  "software": {
    "name": "FHIR Patient Portal",
    "version": "1.0.0"
  },
  "fhirVersion": "4.0.1",
  "format": ["json", "xml"],
  "rest": [
    {
      "mode": "server",
      "resource": [
        {
          "type": "Patient",
          "interaction": [
            { "code": "read" },
            { "code": "search-type" }
          ]
        }
      ]
    }
  ]
}`
      },
      {
        id: 'fhir-batch',
        name: 'Batch Operations',
        method: 'POST',
        path: '/',
        summary: 'Performs multi-resource batch operations.',
        requestPayload: `{
  "resourceType": "Bundle",
  "type": "batch",
  "entry": [
    {
      "request": { "method": "GET", "url": "Patient/patient-uuid-123" }
    },
    {
      "request": { "method": "GET", "url": "Observation?patient=patient-uuid-123" }
    }
  ]
}`
      }
    ]
  },
  {
    key: 'kafka',
    name: 'Kafka Communication Patterns',
    baseUrl: '',
    description: 'Documented topic strategy, schemas, and operational considerations.',
    endpoints: [
      {
        id: 'kafka-topics',
        name: 'Topic Architecture',
        method: 'DESIGN',
        path: 'topic-architecture',
        summary: 'Naming conventions and example topic catalogues.',
        responsePayload: `Structure: {service}.{entity}.{action}.{version}\nExamples: patient.registered.v1, observation.created.v1, audit.logged.v1`
      },
      {
        id: 'kafka-event-schema',
        name: 'Core Event Schema',
        method: 'DESIGN',
        path: 'event-schema',
        summary: 'Canonical JSON structure enforced across events.',
        responsePayload: `{
  "eventId": "event-uuid-123",
  "eventType": "patient.registered.v1",
  "eventVersion": "1.0",
  "timestamp": "2023-09-01T12:30:45Z",
  "source": {
    "service": "patient-service",
    "version": "2.1.0",
    "instance": "patient-service-pod-3"
  },
  "subject": {
    "type": "Patient",
    "id": "patient-uuid-123",
    "tenantId": "tenant-clinic-001"
  },
  "data": {
    "action": "created",
    "userId": "user-uuid-456",
    "previousState": null,
    "currentState": {
      "status": "active",
      "registrationComplete": true
    }
  },
  "metadata": {
    "correlationId": "corr-uuid-789",
    "causationId": "cause-uuid-101",
    "sessionId": "session-uuid-202",
    "traceId": "trace-uuid-303",
    "priority": "normal",
    "retryCount": 0
  },
  "compliance": {
    "dataClassification": "PHI",
    "retentionPeriod": "P7Y",
    "encryptionRequired": true,
    "auditRequired": true
  }
}`
      },
      {
        id: 'kafka-topic-config',
        name: 'Topic Configurations',
        method: 'DESIGN',
        path: 'topic-configurations',
        summary: 'Partitioning, retention, and compression strategies across services.',
        responsePayload: `patient.lifecycle.v1 => partitions: 12, replication: 3, retentionMs: 604800000\nobservation.clinical.v1 => partitions: 24, compression: lz4\nsecurity.events.v1 => partitions: 16, cleanupPolicy: compact`
      },
      {
        id: 'kafka-dlq',
        name: 'Dead Letter Queue',
        method: 'DESIGN',
        path: 'dlq',
        summary: 'Retry policies and alerting for failed events.',
        responsePayload: `dlq.failed-events.v1 => partitions: 4, retentionMs: 604800000, retry max: 3, exponential backoff`
      },
      {
        id: 'kafka-processing',
        name: 'Consumer Processing Patterns',
        method: 'DESIGN',
        path: 'consumers',
        summary: 'Realtime, batch, and compliance consumer archetypes.',
        responsePayload: `patient-service-realtime => topics: hl7.message.received.v1, user.registered.v1\nnotification-service-immediate => priority queues by severity\nanalytics-service-batch => windowDuration PT5M`
      },
      {
        id: 'kafka-monitoring',
        name: 'Performance Monitoring and Alerting',
        method: 'DESIGN',
        path: 'monitoring',
        summary: 'Metrics, health checks, and alert thresholds.',
        responsePayload: `Monitor consumer_lag > 10000 for PT5M (warning)\nAlert error_rate > 0.05 for PT2M (critical)\nHealth checks: latency, lag, disk usage, replication`
      },
      {
        id: 'kafka-security',
        name: 'Security Configuration',
        method: 'DESIGN',
        path: 'security',
        summary: 'Kafka ACLs, encryption, and schema registry governance.',
        responsePayload: `Protocol: SASL_SSL (SCRAM-SHA-512)\nEncryption: TLS 1.3 in transit, AES-256-GCM at rest\nSchema Registry: BACKWARD compatibility, TopicNameStrategy`
      }
    ]
  }
];

servicesData.forEach((service) => {
  service.endpoints.forEach((endpoint) => {
    endpoint.fullPath = `${service.baseUrl}${endpoint.path}`.replace(/\/\/$/, '/');
  });
});

export default servicesData;
