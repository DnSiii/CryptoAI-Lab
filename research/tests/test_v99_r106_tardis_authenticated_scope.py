"""Negative controls for bounded Tardis archive entitlement scope (NO TRADES)."""
import json
import unittest
import urllib.error
from research_tools.v99_r106_tardis_authenticated_scope import check, DATES


class FakeResponse:
    def __init__(self, status, data=b"\x1f\x8b", content_range=None):
        self.status = status
        self.data = data
        self.headers = {"Content-Range": "bytes 0-1/999"} if status == 206 else {}
        if content_range is not None:
            self.headers["Content-Range"] = content_range

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n):
        assert n == 2, "MUST_NOT_DOWNLOAD_FULL_PAID_ARCHIVE"
        return self.data[:n]


class FakeOpener:
    def __init__(self, denied_date=None, empty_date=None, bad_body_date=None,
                 ignored_range_date=None, malformed_range_date=None):
        self.denied_date = denied_date
        self.empty_date = empty_date
        self.bad_body_date = bad_body_date
        self.ignored_range_date = ignored_range_date
        self.malformed_range_date = malformed_range_date
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request.full_url, request.get_method(),
                           request.get_header("Range")))
        assert timeout <= 20
        assert request.get_header("Authorization") == "Bearer secret-test-key"
        if "api-key-info" in request.full_url:
            return FakeResponse(200)
        day = "-".join(request.full_url.split("/")[-4:-1])
        if day == self.denied_date:
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)
        if request.get_method() == "GET":
            assert request.get_header("Range") == "bytes=0-1"
            status = 200 if day == self.ignored_range_date else 206
            body = (b"" if day == self.empty_date else
                    b"<html>" if day == self.bad_body_date else b"\x1f\x8b")
            content_range = "bytes 3-4/999" if day == self.malformed_range_date else None
            return FakeResponse(status, body, content_range)
        return FakeResponse(200)


class ScopeProbeTests(unittest.TestCase):
    def test_no_key_fails_without_network(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("NETWORK_WITHOUT_KEY")
        result = check(key="", opener=forbidden)
        self.assertEqual(result["status"], "BLOCKED_NO_AUTHENTICATED_ARCHIVE_KEY_CONFIGURED")
        self.assertEqual(result["probes"], [])

    def test_three_non_sample_dates_only_access_not_full_proof(self):
        opener = FakeOpener()
        result = check(key="secret-test-key", opener=opener)
        self.assertEqual(result["status"], "ACCESS_PROBE_ONLY_NOT_ARCHIVE_CERTIFIED")
        self.assertEqual([p["date"] for p in result["probes"]], list(DATES))
        self.assertEqual(len(opener.calls), 7)
        self.assertTrue(all(p["bounded_source_access_only"] for p in result["probes"]))
        self.assertFalse(result["complete_2021_2023_archive_verified"])
        self.assertFalse(result["economic_train_executed"])
        self.assertFalse(result["promotion_authorized"])
        self.assertNotIn("secret-test-key", json.dumps(result))

    def test_denied_2021_blocks_even_when_2023_accessible(self):
        result = check(key="secret-test-key", opener=FakeOpener(denied_date=DATES[0]))
        self.assertEqual(result["status"], "BLOCKED_ENTITLEMENT_OR_HISTORICAL_SOURCE")
        self.assertEqual(result["probes"][0]["bounded_get_http"], 403)
        self.assertFalse(result["source_entitlement_verified"])

    def test_empty_partial_response_is_not_access(self):
        result = check(key="secret-test-key", opener=FakeOpener(empty_date=DATES[-1]))
        self.assertEqual(result["status"], "BLOCKED_ENTITLEMENT_OR_HISTORICAL_SOURCE")
        self.assertFalse(result["probes"][-1]["bounded_get_nonempty"])

    def test_html_error_page_with_206_is_not_archive(self):
        result = check(key="secret-test-key", opener=FakeOpener(bad_body_date=DATES[0]))
        self.assertEqual(result["status"], "BLOCKED_ENTITLEMENT_OR_HISTORICAL_SOURCE")
        self.assertFalse(result["probes"][0]["gzip_magic"])

    def test_ignored_range_with_http_200_is_not_archive(self):
        result = check(key="secret-test-key", opener=FakeOpener(ignored_range_date=DATES[1]))
        self.assertEqual(result["status"], "BLOCKED_ENTITLEMENT_OR_HISTORICAL_SOURCE")
        self.assertFalse(result["probes"][1]["bounded_206"])

    def test_wrong_content_range_is_not_archive(self):
        result = check(key="secret-test-key", opener=FakeOpener(malformed_range_date=DATES[2]))
        self.assertEqual(result["status"], "BLOCKED_ENTITLEMENT_OR_HISTORICAL_SOURCE")
        self.assertFalse(result["probes"][2]["bounded_206"])

    def test_unsupported_http_head_does_not_replace_bounded_get(self):
        class HeadUnsupported(FakeOpener):
            def __call__(self, request, timeout):
                if request.get_method() == "HEAD":
                    raise urllib.error.HTTPError(request.full_url, 405, "Method Not Allowed", {}, None)
                return super().__call__(request, timeout)
        result = check(key="secret-test-key", opener=HeadUnsupported())
        self.assertEqual(result["status"], "ACCESS_PROBE_ONLY_NOT_ARCHIVE_CERTIFIED")
        self.assertEqual(result["probes"][0]["head_http"], 405)


if __name__ == "__main__":
    unittest.main()
