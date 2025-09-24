from __future__ import annotations

from unittest.mock import patch

from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone

from services.sample_utils import (
    deep_merge,
    ensure_list,
    generate_identifier,
    isoformat_now,
    parse_iso_date,
    parse_iso_datetime,
)


class IsoformatNowTests(SimpleTestCase):
    def test_returns_utc_timestamp_with_z_suffix(self) -> None:
        fixed = timezone.datetime(2023, 9, 1, 12, 30, 45, tzinfo=timezone.utc)
        with patch("services.sample_utils.timezone.now", return_value=fixed):
            self.assertEqual(isoformat_now(), "2023-09-01T12:30:45Z")


class GenerateIdentifierTests(SimpleTestCase):
    def test_uses_override_when_provided(self) -> None:
        self.assertEqual(generate_identifier("patient", override="custom-id"), "custom-id")

    def test_generates_unique_identifier_with_prefix(self) -> None:
        identifier = generate_identifier("patient")
        self.assertTrue(identifier.startswith("patient-"))


class DeepMergeTests(SimpleTestCase):
    def test_merges_nested_mappings_without_mutating_base(self) -> None:
        base = {"nested": {"value": 1}, "keep": 2}
        overrides = {"nested": {"extra": 3}}

        result = deep_merge(base, overrides)

        self.assertEqual(result["nested"], {"value": 1, "extra": 3})
        self.assertEqual(result["keep"], 2)
        # Ensure the base mapping was not modified in place
        self.assertEqual(base, {"nested": {"value": 1}, "keep": 2})


class EnsureListTests(SimpleTestCase):
    def test_returns_existing_non_empty_list(self) -> None:
        values = [1]
        self.assertIs(ensure_list(values, [2]), values)

    def test_returns_copy_of_default_for_empty_or_invalid_values(self) -> None:
        default = ["fallback"]
        result = ensure_list([], default)

        self.assertEqual(result, default)
        self.assertIsNot(result, default)

        result_none = ensure_list(None, default)
        self.assertEqual(result_none, default)
        self.assertIsNot(result_none, default)


class ParseIsoDateTimeTests(SimpleTestCase):
    def test_parse_iso_datetime_handles_z_suffix(self) -> None:
        parsed = parse_iso_datetime("2023-09-01T12:30:45Z")
        self.assertEqual(parsed, timezone.datetime(2023, 9, 1, 12, 30, 45, tzinfo=None))

    def test_parse_iso_datetime_returns_none_for_invalid(self) -> None:
        self.assertIsNone(parse_iso_datetime("not-a-date"))

    def test_parse_iso_date_returns_date_component(self) -> None:
        parsed = parse_iso_date("2023-09-01")
        self.assertEqual(parsed, timezone.datetime(2023, 9, 1).date())
