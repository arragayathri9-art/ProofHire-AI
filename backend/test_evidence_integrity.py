import sys
import unittest
from services.url_inspector import inspect_url
from services.evidence_intelligence import sanitize_uninspected_text, verify_claim_with_gemini
from schemas.schemas import GeminiVerificationAssessment

class TestEvidenceIntegrity(unittest.TestCase):
    def test_inspect_url_submitted_only(self):
        content, status = inspect_url("https://example.com/some/repo", auto_inspect=False)
        self.assertEqual(status, "submitted_only")
        self.assertIn("A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.", content)

    def test_inspect_url_invalid(self):
        content, status = inspect_url("https://nonexistent-domain-proofhire-test-xyz-999.org", auto_inspect=True)
        self.assertEqual(status, "retrieval_failed")
        self.assertIn("A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.", content)

    def test_sanitize_uninspected_text_prohibited_phrases(self):
        raw_text_1 = "The candidate provided a URL which confirms the existence of the portfolio project."
        sanitized_1 = sanitize_uninspected_text(raw_text_1, has_retrieved_evidence=False)
        self.assertNotIn("confirms the existence", sanitized_1)
        self.assertIn("A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.", sanitized_1)

        raw_text_2 = "This repository verifies the deployment on Vercel."
        sanitized_2 = sanitize_uninspected_text(raw_text_2, has_retrieved_evidence=False)
        self.assertNotIn("verifies the deployment", sanitized_2)
        self.assertIn("A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.", sanitized_2)

        raw_text_3 = "The link proves the project was completed successfully."
        sanitized_3 = sanitize_uninspected_text(raw_text_3, has_retrieved_evidence=False)
        self.assertNotIn("proves the project", sanitized_3)
        self.assertIn("A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.", sanitized_3)

    def test_zero_evidence_remains_needs_verification(self):
        # Empty evidence texts must immediately return 'Needs Verification'
        res = verify_claim_with_gemini("Built a full-stack microservice", [], "Resume text")
        self.assertEqual(res.evidence_level, "Needs Verification")
        self.assertIn("No additional supporting evidence has been provided yet.", res.what_is_missing)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEvidenceIntegrity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("ALL INTEGRITY TESTS PASSED!")
