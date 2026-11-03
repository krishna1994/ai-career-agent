import unittest
from unittest.mock import MagicMock, patch
import os

# Mocking config before importing other modules
import sys
from types import ModuleType

mock_config = ModuleType('config')
mock_config.use_ai_features = True
mock_config.ai_api_key = "mock_key"
mock_config.ai_model = "gpt-4o"
mock_config.min_ats_score = 3
mock_config.enable_resume_tailoring = True
sys.modules['config'] = mock_config

from ai_engine import AIEngine
from db_manager import DBManager

class TestFullFlow(unittest.TestCase):
    def setUp(self):
        self.ai = AIEngine()
        self.test_db_path = os.path.join("data", "test_apps.db")
        # Ensure a clean database for every test run so assertions on row
        # counts are deterministic and not polluted by previous runs.
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = DBManager(db_path=self.test_db_path)
        self.resume = "Experienced Python Developer with 5 years in AI and Automation."
        self.jd = "Looking for a Senior Python Engineer with AI experience."

    def tearDown(self):
        # On Windows, the sqlite3 file handle may briefly remain locked even
        # after the connection context manager exits. Retry/ignore failures
        # so test cleanup never masks the actual test result.
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_ai_integration_flow(self):
        print("\n--- Starting Mock Full Flow Test ---")
        
        # 1. Mock the LLM response for ATS Scoring
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": '{"score": 5, "reason": "Perfect match for AI and Python skills"}'}}]
            }
            mock_post.return_value = mock_response

            # Step A: ATS Scoring
            print("Step 1: Scoring Job...")
            score_data = self.ai.get_ats_score(self.resume, self.jd)
            print(f"AI Score: {score_data['score']}/5 - {score_data['reason']}")
            self.assertEqual(score_data['score'], 5)

            # Step B: Decision Logic
            if score_data['score'] >= 3:
                print("Decision: ✅ Match found. Proceeding to apply.")
                
                # Step C: Resume Tailoring
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Tailored Resume: Expert in AI and Python..."}}]
                }
                print("Step 2: Tailoring Resume...")
                tailored_resume = self.ai.tailor_resume(self.resume, self.jd)
                print(f"Tailored Result: {tailored_resume[:50]}...")
                self.assertIsNotNone(tailored_resume)

                # Step D: Database Logging
                print("Step 3: Logging to Database...")
                self.db.log_application(
                    job_id="12345",
                    job_title="Senior Python Engineer",
                    company="AI Corp",
                    location="Remote",
                    url="https://linkedin.com/jobs/12345",
                    ats_score=score_data['score'],
                    ats_reason=score_data['reason'],
                    status="Applied",
                    tailored=True
                )
                
                # Verify DB entry
                apps = self.db.get_all_applications()
                self.assertEqual(len(apps), 1)
                self.assertEqual(apps[0]['job_id'], "12345")
                print("✅ Database entry verified.")
            else:
                self.fail("Bot skipped a high-match job")

        print("--- Full Flow Mock Test Passed Successfully! ---\n")

if __name__ == "__main__":
    unittest.main()