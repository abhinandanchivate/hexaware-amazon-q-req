from __future__ import annotations

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient


SQLITE_DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


@override_settings(DATABASES=SQLITE_DATABASES)
class HL7ParserViewTests(SimpleTestCase):
    client_class = APIClient

    def test_ingest_merges_payload_with_defaults(self) -> None:
        payload = {
            "status": "custom-status",
            "fhirResources": [
                {
                    "identifier": [{"value": "MRN12345"}],
                    "name": [{"family": "Doe", "given": ["John"]}],
                }
            ],
        }

        response = self.client.post("/api/v1/hl7-parser/ingest", payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "custom-status")
        self.assertEqual(
            response.data["fhirResources"][0]["identifier"], [{"value": "MRN12345"}]
        )
        self.assertIn("messageId", response.data)
        self.assertIn("timestamp", response.data)


@override_settings(DATABASES=SQLITE_DATABASES)
class PatientViewTests(SimpleTestCase):
    client_class = APIClient

    def test_registration_populates_default_identifiers_and_names(self) -> None:
        payload = {
            "identifier": [],
            "name": [],
            "gender": "male",
            "birthDate": "1980-01-15",
        }

        response = self.client.post("/api/v1/patients/", payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["gender"], "male")
        self.assertEqual(response.data["identifier"][0]["value"], "MRN-SAMPLE")
        self.assertEqual(response.data["name"][0]["family"], "Sample")
        self.assertIn("meta", response.data)
        self.assertIn("lastUpdated", response.data["meta"])


@override_settings(DATABASES=SQLITE_DATABASES)
class ObservationViewTests(SimpleTestCase):
    client_class = APIClient

    def test_lab_results_default_entry_contains_location(self) -> None:
        response = self.client.post("/api/v1/observations/lab-results", {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["resourceType"], "Bundle")
        self.assertTrue(response.data["entry"])
        entry = response.data["entry"][0]
        self.assertIn("response", entry)
        self.assertIn("Observation/", entry["response"]["location"])


@override_settings(DATABASES=SQLITE_DATABASES)
class KafkaViewTests(SimpleTestCase):
    client_class = APIClient

    def test_event_schema_returns_compliance_metadata(self) -> None:
        response = self.client.get("/api/v1/kafka/events/schema")

        self.assertEqual(response.status_code, 200)
        self.assertIn("compliance", response.data)
        self.assertEqual(response.data["eventType"], "patient.registered.v1")

    def test_configuration_supports_section_filter(self) -> None:
        response = self.client.get("/api/v1/kafka/config", {"section": "topics"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("patient.lifecycle.v1", response.data)

    def test_governance_includes_retry_policy(self) -> None:
        response = self.client.get("/api/v1/kafka/governance")

        self.assertEqual(response.status_code, 200)
        self.assertIn("retryPolicy", response.data)
