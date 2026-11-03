"""
test_full_flow_simulation.py - End-to-End System Simulation
This script simulates the entire bot lifecycle from job discovery to DB logging
without requiring live credentials or API keys.
"""

import os
import sys
from unittest.mock import MagicMock, patch
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

# Mocking config before imports to avoid API key errors
import config
config.use_ai_features = True
config.email = "test@example.com"
config.password = "testpass"
config.ai_api_key = "sk-mock-key"
config.dryRun = False
config.maxApplicationsPerRun = 5
config.min_ats_score = 3
config.max_skill_gaps = 5

from ai_engine import AIEngine
from skill_analyzer import SkillAnalyzer
from db_manager import DBManager
import utils

# ── Mock Data ──
MOCK_RESUME = "Krishna Singh\nSenior Software Engineer\nSkills: Python, FastAPI, Docker, Kubernetes, AWS"
MOCK_JOBS = [
    {
        "id": "job_001",
        "title": "Senior AI Engineer",
        "company": "OpenAI",
        "url": "https://linkedin.com/jobs/1",
        "jd": "Requirements: Python, FastAPI, Kubernetes, PyTorch, LLMs, AWS"
    },
    {
        "id": "job_002",
        "title": "Backend Developer",
        "company": "MidCorp",
        "url": "https://linkedin.com/jobs/2",
        "jd": "Requirements: Python, SQL, Git, Linux"
    },
    {
        "id": "job_003",
        "title": "Frontend React Dev",
        "company": "WebStudio",
        "url": "https://linkedin.com/jobs/3",
        "jd": "Requirements: React, TypeScript, CSS, Figma, Tailwind"
    }
]

def print_step(step_name, status="PROCESSING"):
    color = "\033[93m" if status == "PROCESSING" else "\033[92m" if status == "SUCCESS" else "\033[91m"
    print(f"{color}[{status}]\033[0m {step_name}")

def run_simulation():
    print("\n" + "="*60)
    print("  🤖 AI Career Agent - FULL FLOW SIMULATION")
    print("="*60)
    
    # Initialize Components
    db = DBManager()
    # Ensure the table is created before we start logging
    db._init_db() 
    analyzer = SkillAnalyzer()
    
    # Mock AIEngine to avoid API calls but simulate realistic responses
    mock_ai = MagicMock(spec=AIEngine)
    mock_ai.enabled = True
    
    def mock_get_score(resume, jd):
        if "AI Engineer" in jd or "AI Engineer" in "Senior AI Engineer":
            return {"score": 5, "reason": "Perfect match for AI/ML stack"}
        if "Frontend" in jd or "React" in jd:
            return {"score": 1, "reason": "No frontend experience found"}
        return {"score": 3, "reason": "General backend match"}

    def mock_answer(resume, jd, q):
        return f"AI-generated professional answer for: {q}"

    def mock_tailor(resume, jd):
        return f"TAILORED RESUME based on {jd[:20]}..."

    mock_ai.get_ats_score.side_effect = mock_get_score
    mock_ai.answer_question.side_effect = mock_answer
    mock_ai.tailor_resume.side_effect = mock_tailor

    applied_count = 0

    for i, job in enumerate(MOCK_JOBS, 1):
        print(f"\n--- Processing Job {i}: {job['title']} at {job['company']} ---")
        
        # Step 1: Discovery
        print_step("Job Discovery", "SUCCESS")
        
        # Step 2: Skill Gap Analysis (Deterministic)
        print_step("Skill Gap Analysis", "PROCESSING")
        skills = analyzer.extract_skills_from_jd(job['jd'])
        gaps = analyzer.analyze_gaps(skills, MOCK_RESUME)
        gap_count = len(gaps['gaps'])
        print(f"   Found {len(skills)} skills. Gaps: {gap_count}")
        
        if gap_count > config.max_skill_gaps:
            print_step("Skill Gate", "FAILED (Too many gaps)")
            db.log_application(job['id'], job['title'], job['company'], "Remote", job['url'], 0, "Too many gaps", "Skipped")
            continue
        print_step("Skill Gate", "SUCCESS")

        # Step 3: AI Scoring
        print_step("AI ATS Scoring", "PROCESSING")
        score_data = mock_ai.get_ats_score(MOCK_RESUME, job['jd'])
        score = score_data['score']
        print(f"   AI Score: {score}/5 - {score_data['reason']}")
        
        if score < config.min_ats_score:
            print_step("Score Gate", "FAILED (Low score)")
            db.log_application(job['id'], job['title'], job['company'], "Remote", job['url'], score, score_data['reason'], "Skipped")
            continue
        print_step("Score Gate", "SUCCESS")

        # Step 4: AI Tailoring & Form Filling
        print_step("AI Tailoring", "PROCESSING")
        _ = mock_ai.tailor_resume(MOCK_RESUME, job['jd'])
        
        print_step("AI Form Filling", "PROCESSING")
        _ = mock_ai.answer_question(MOCK_RESUME, job['jd'], "Why this role?")
        
        # Step 5: Submission (Mocked)
        print_step("Browser Submission", "SUCCESS")
        db.log_application(job['id'], job['title'], job['company'], "Remote", job['url'], score, score_data['reason'], "Applied")
        applied_count += 1

    print("\n" + "="*60)
    print(f"  Simulation Complete: Applied to {applied_count}/{len(MOCK_JOBS)} jobs.")
    print("="*60)

    # Final Verification: Check the DB
    print("\n🔍 Verifying Database Logs...")
    # Use the same path as DBManager
    db_path = getattr(db, 'db_path', 'data/applications.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT job_title, ats_score, status FROM applications ORDER BY id DESC LIMIT 3")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   DB Entry -> Job: {row[0]} | Score: {row[1]} | Status: {row[2]}")
    conn.close()

if __name__ == "__main__":
    # Ensure data dir exists
    os.makedirs('AI_Career_Agent/data', exist_ok=True)
    run_simulation()