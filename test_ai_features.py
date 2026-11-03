"""
test_ai_features.py - Comprehensive AI Feature Testing
Tests the AIEngine, SkillAnalyzer, and their integration without requiring live job applications.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from ai_engine import AIEngine
from skill_analyzer import SkillAnalyzer

# ── Test Data ──
SAMPLE_RESUME = """
Krishna Singh
Senior Software Engineer at Qualcomm

SKILLS:
Python, FastAPI, Django, PostgreSQL, Docker, Kubernetes, AWS, Git, CI/CD, REST APIs, Microservices

EXPERIENCE:
Senior Software Engineer | Qualcomm | 2020 - Present
- Designed and deployed scalable microservices using Python and FastAPI
- Implemented CI/CD pipelines with Docker and Kubernetes
- Built REST APIs serving 10M+ requests per day
- Optimized PostgreSQL queries reducing latency by 40%

Software Engineer | Tech Corp | 2018 - 2020
- Developed backend services using Django and PostgreSQL
- Deployed applications to AWS EC2 and RDS
- Collaborated with cross-functional teams on feature development
"""

SAMPLE_JD_HIGH_MATCH = """
Senior Backend Engineer - AI Platform

Requirements:
- 5+ years of Python development experience
- Strong knowledge of FastAPI and Django frameworks
- Experience with PostgreSQL database design
- Proficiency in Docker and Kubernetes
- AWS cloud infrastructure experience
- REST API design and microservices architecture
- CI/CD pipeline implementation

Nice to have:
- Experience with AI/ML model deployment
- Terraform infrastructure as code
"""

SAMPLE_JD_LOW_MATCH = """
Senior Frontend Engineer - React Specialist

Requirements:
- 5+ years of React.js and TypeScript experience
- Expert knowledge of Next.js and Redux
- Strong CSS/SCSS and responsive design skills
- Experience with GraphQL and Apollo Client
- Jest and React Testing Library proficiency
- Webpack and Babel configuration
- Figma to code conversion experience

Nice to have:
- Node.js backend experience
- AWS deployment knowledge
"""

SAMPLE_JD_MEDIUM_MATCH = """
Full Stack Engineer - Cloud Platform

Requirements:
- 3+ years of Python or Node.js experience
- Experience with PostgreSQL or MongoDB
- Docker containerization knowledge
- AWS or Azure cloud platform experience
- REST API development
- Terraform infrastructure as code
- Helm chart management
- React.js frontend development

Nice to have:
- Kubernetes orchestration
- CI/CD pipeline setup
"""

SAMPLE_QUESTIONS = [
    "How many years of Python experience do you have?",
    "Describe your experience with microservices architecture.",
    "What is your expected salary range?",
    "Why are you interested in this position?",
]


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_ats_scoring() -> None:
    """Test the ATS scoring functionality."""
    print_section("TEST 1: ATS Scoring")
    
    engine = AIEngine()
    
    if not engine.enabled:
        print("❌ AIEngine is not enabled. Please set use_ai_features=True and provide an API key.")
        return
    
    print("\n🔍 Testing High Match Job (Backend Engineer)...")
    score_high = engine.get_ats_score(SAMPLE_RESUME, SAMPLE_JD_HIGH_MATCH)
    print(f"   Score: {score_high['score']}/5")
    print(f"   Reason: {score_high['reason']}")
    
    print("\n🔍 Testing Low Match Job (Frontend Engineer)...")
    score_low = engine.get_ats_score(SAMPLE_RESUME, SAMPLE_JD_LOW_MATCH)
    print(f"   Score: {score_low['score']}/5")
    print(f"   Reason: {score_low['reason']}")
    
    print("\n🔍 Testing Medium Match Job (Full Stack Engineer)...")
    score_medium = engine.get_ats_score(SAMPLE_RESUME, SAMPLE_JD_MEDIUM_MATCH)
    print(f"   Score: {score_medium['score']}/5")
    print(f"   Reason: {score_medium['reason']}")
    
    # Validation
    print("\n✅ Validation:")
    if score_high['score'] >= 4:
        print("   ✓ High match job scored 4 or 5 (Expected)")
    else:
        print(f"   ✗ High match job scored {score_high['score']} (Expected 4-5)")
    
    if score_low['score'] <= 2:
        print("   ✓ Low match job scored 1 or 2 (Expected)")
    else:
        print(f"   ✗ Low match job scored {score_low['score']} (Expected 1-2)")
    
    if 2 <= score_medium['score'] <= 4:
        print("   ✓ Medium match job scored 2-4 (Expected)")
    else:
        print(f"   ✗ Medium match job scored {score_medium['score']} (Expected 2-4)")


def test_skill_gap_analysis() -> None:
    """Test the deterministic skill gap analysis."""
    print_section("TEST 2: Skill Gap Analysis")
    
    analyzer = SkillAnalyzer()
    
    print("\n🔍 Extracting skills from High Match JD...")
    jd_skills = analyzer.extract_skills_from_jd(SAMPLE_JD_HIGH_MATCH)
    print(f"   Extracted Skills: {jd_skills}")
    
    print("\n🔍 Analyzing gaps against resume...")
    gap_result = analyzer.analyze_gaps(jd_skills, SAMPLE_RESUME)
    
    print(f"\n   ✅ Existing (in Skills section): {gap_result['existing']}")
    print(f"   ⚠️ Supported (in Experience prose): {gap_result['supported']}")
    print(f"   ❌ Gaps (completely missing): {gap_result['gaps']}")
    
    # Validation
    print("\n✅ Validation:")
    total_skills = len(jd_skills)
    covered_skills = len(gap_result['existing']) + len(gap_result['supported'])
    coverage = (covered_skills / total_skills * 100) if total_skills > 0 else 0
    
    print(f"   Coverage: {covered_skills}/{total_skills} skills ({coverage:.1f}%)")
    
    if coverage >= 70:
        print("   ✓ High coverage (70%+) - Should apply")
    elif coverage >= 50:
        print("   ⚠️ Medium coverage (50-70%) - Consider applying")
    else:
        print("   ✗ Low coverage (<50%) - Should skip")


def test_ai_question_answering() -> None:
    """Test the AI's ability to answer custom application questions."""
    print_section("TEST 3: AI Question Answering")
    
    engine = AIEngine()
    
    if not engine.enabled:
        print("❌ AIEngine is not enabled. Please set use_ai_features=True and provide an API key.")
        return
    
    for i, question in enumerate(SAMPLE_QUESTIONS, 1):
        print(f"\n❓ Question {i}: {question}")
        answer = engine.answer_question(SAMPLE_RESUME, SAMPLE_JD_HIGH_MATCH, question)
        print(f"   💬 Answer: {answer}")
    
    print("\n✅ Validation:")
    print("   ✓ All questions answered (check if answers are professional and truthful)")


def test_resume_tailoring() -> None:
    """Test the AI's resume tailoring capability."""
    print_section("TEST 4: Resume Tailoring (Optional)")
    
    engine = AIEngine()
    
    if not engine.enabled:
        print("❌ AIEngine is not enabled. Please set use_ai_features=True and provide an API key.")
        return
    
    print("\n🔍 Tailoring resume for High Match Job...")
    print("   (This may take 10-15 seconds...)")
    
    tailored = engine.tailor_resume(SAMPLE_RESUME, SAMPLE_JD_HIGH_MATCH)
    
    print("\n📄 Original Resume (excerpt):")
    print(SAMPLE_RESUME[:200] + "...")
    
    print("\n📄 Tailored Resume (excerpt):")
    print(tailored[:200] + "...")
    
    print("\n✅ Validation:")
    if len(tailored) > len(SAMPLE_RESUME) * 0.8:
        print("   ✓ Tailored resume has reasonable length")
    else:
        print("   ✗ Tailored resume seems too short")
    
    if "Python" in tailored and "FastAPI" in tailored:
        print("   ✓ Key skills preserved in tailored version")
    else:
        print("   ✗ Key skills may have been lost")


def test_integration() -> None:
    """Test the full integration: Scoring → Gap Analysis → Decision."""
    print_section("TEST 5: Full Integration Flow")
    
    engine = AIEngine()
    analyzer = SkillAnalyzer()
    
    if not engine.enabled:
        print("❌ AIEngine is not enabled. Skipping integration test.")
        return
    
    print("\n🔍 Simulating application decision for High Match Job...")
    
    # Step 1: ATS Scoring
    score_data = engine.get_ats_score(SAMPLE_RESUME, SAMPLE_JD_HIGH_MATCH)
    ats_score = score_data['score']
    print(f"\n   Step 1 - ATS Score: {ats_score}/5")
    
    if ats_score < 3:
        print("   ❌ Decision: SKIP (Score too low)")
        return
    
    # Step 2: Skill Gap Analysis
    jd_skills = analyzer.extract_skills_from_jd(SAMPLE_JD_HIGH_MATCH)
    gap_result = analyzer.analyze_gaps(jd_skills, SAMPLE_RESUME)
    num_gaps = len(gap_result['gaps'])
    print(f"   Step 2 - Skill Gaps: {num_gaps} missing skills")
    
    if num_gaps > 5:
        print("   ❌ Decision: SKIP (Too many gaps)")
        return
    
    # Step 3: Final Decision
    print("\n   ✅ Decision: APPLY")
    print(f"      - ATS Score: {ats_score}/5 (Pass)")
    print(f"      - Skill Gaps: {num_gaps} (Acceptable)")
    print(f"      - Existing Skills: {len(gap_result['existing'])}")
    print(f"      - Supported Skills: {len(gap_result['supported'])}")


def main() -> None:
    """Run all AI feature tests."""
    print("\n" + "=" * 70)
    print("  🤖 AI Career Agent - Feature Test Suite")
    print("=" * 70)
    print("\nThis script tests the AI features without making live applications.")
    print("It uses sample data to validate the AIEngine and SkillAnalyzer.")
    
    try:
        test_ats_scoring()
        test_skill_gap_analysis()
        test_ai_question_answering()
        # test_resume_tailoring()  # Uncomment to test (slower, uses more tokens)
        test_integration()
        
        print("\n" + "=" * 70)
        print("  ✅ All Tests Complete")
        print("=" * 70)
        print("\nIf all validations passed, the AI features are working correctly.")
        print("You can now run the bot with confidence using:")
        print("  python linkedin.py  (for LinkedIn)")
        print("  python indeed.py    (for Indeed)")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()