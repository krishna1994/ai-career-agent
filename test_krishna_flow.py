import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

# 1. Setup Mock Config to simulate your environment
mock_config = ModuleType('config')
mock_config.use_ai_features = True
mock_config.ai_api_key = "mock_key"
mock_config.ai_model = "gpt-4o"
mock_config.min_ats_score = 3
mock_config.enable_resume_tailoring = True
sys.modules['config'] = mock_config

from ai_engine import AIEngine
from db_manager import DBManager

def run_simulation():
    ai = AIEngine()
    db = DBManager(db_path="data/krishna_test.db")
    
    # Your actual resume content
    resume_text = """
    Krishna Singh - Senior Software Engineer
    Experience: 9+ years. 
    Current: Qualcomm (Senior Software Engineer).
    Skills: Python, FastAPI, Django, PostgreSQL, OpenAI APIs, LLM Integration, Semantic Search, Azure, AWS.
    Education: MSc Artificial Intelligence.
    """
    
    # A sample high-match job description
    job_description = """
    We are looking for a Senior AI Engineer. 
    Requirements: 
    - Strong expertise in Python and FastAPI.
    - Experience integrating LLMs and OpenAI APIs into production.
    - Knowledge of PostgreSQL and cloud platforms (Azure/AWS).
    - Experience with semantic search and prompt engineering.
    """

    print("🚀 Starting Simulation for Krishna Singh...\n")

    with patch('requests.post') as mock_post:
        # Mocking a high-match AI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"score": 5, "reason": "Exceptional match. Candidate has direct experience with OpenAI APIs, FastAPI, and an MSc in AI."}'}}]
        }
        mock_post.return_value = mock_response

        # Step 1: ATS Scoring
        print("🔍 Step 1: AI is analyzing your resume against the Job Description...")
        score_data = ai.get_ats_score(resume_text, job_description)
        print(f"✅ AI Score: {score_data['score']}/5")
        print(f"📝 Reason: {score_data['reason']}")

        if score_data['score'] >= 3:
            print("\n🎯 Decision: High Match! Proceeding to application phase...")
            
            # Step 2: Resume Tailoring
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "TAILORED RESUME: Senior AI Engineer with 9+ years experience... Specialized in OpenAI API integration and FastAPI..."}}]
            }
            print("✍️ Step 2: AI is tailoring your resume for this specific role...")
            tailored = ai.tailor_resume(resume_text, job_description)
            print(f"✨ Tailored Snippet: {tailored[:100]}...")

            # Step 3: Database Logging
            print("\n💾 Step 3: Logging application to database...")
            db.log_application(
                job_id="KRISHNA_TEST_001",
                job_title="Senior AI Engineer",
                company="Sample AI Corp",
                location="Remote",
                url="https://linkedin.com/jobs/sample",
                ats_score=score_data['score'],
                ats_reason=score_data['reason'],
                status="Applied",
                tailored=True
            )
            print("✅ Application successfully logged to data/krishna_test.db")
        else:
            print("\n❌ Decision: Low match. Skipping this job.")

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_simulation()