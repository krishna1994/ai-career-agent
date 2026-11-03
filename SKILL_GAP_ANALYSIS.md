# 🎯 Skill Gap Analysis

This document explains the **Deterministic Skill Gap Analysis** feature built into AI Career Agent.

---

## 🧠 What is Skill Gap Analysis?

Instead of relying solely on an LLM to "guess" if you're a good fit, the bot uses a **Zero-LLM, regex-based state machine** to:

1. **Extract** a precise list of required skills from the LinkedIn Job Description.
2. **Classify** each skill into three buckets:
   - **Existing:** Explicitly listed in your resume's "Skills" section.
   - **Supported:** Not in your Skills list, but mentioned in your Experience prose.
   - **Gap:** Completely absent from your resume.

---

## 🔍 How It Works

### Step 1: Intelligent JD Parsing
The analyzer uses a **state machine** to identify "Requirements" sections in the JD. It recognizes common headers like:
- "Requirements"
- "What we're looking for"
- "Who you are"
- "You will have"
- "Ideal candidate"

It also knows when to **stop** (e.g., when it hits "Benefits" or "About Us").

### Step 2: Skill Extraction
From the requirements bullets, it extracts **capitalized technical tokens** (e.g., "Python", "Kubernetes", "FastAPI") while filtering out generic boilerplate like:
- "Bachelor's degree"
- "5+ years of experience"
- "Strong communication skills"

### Step 3: Three-Bucket Classification
For each extracted skill, it checks:
1. **Is it in your "Skills" section?** → `existing`
2. **Is it mentioned in your "Experience" prose?** → `supported`
3. **Is it completely absent?** → `gap`

---

## 💡 Why This Matters

### Before (LLM-Only Scoring):
```
AI Score: 4/5 - "Good match for Python and cloud experience"
```
**Problem:** Vague. You don't know *which* skills are missing.

### After (Skill Gap Analysis + LLM):
```
Skill Analysis:
  ✅ Existing: Python, FastAPI, PostgreSQL
  ⚠️ Supported: Kubernetes (mentioned in prose)
  ❌ Gaps: Terraform, Helm

AI Score: 4/5 - "Strong match, but missing Terraform and Helm"
Decision: Apply (only 2 gaps, both learnable)
```
**Benefit:** You know *exactly* why the bot decided to apply or skip.

---

## 🛠️ Integration with the Bot

The `SkillAnalyzer` is called **before** the `AIEngine` in the application flow:

```python
# 1. Extract skills from JD
analyzer = SkillAnalyzer()
jd_skills = analyzer.extract_skills_from_jd(job_description)

# 2. Classify against your resume
gap_analysis = analyzer.analyze_gaps(jd_skills, resume_text)

# 3. Hard-gate: Skip if too many gaps
if len(gap_analysis['gaps']) > 5:
    print("❌ Too many skill gaps. Skipping this job.")
    return

# 4. AI Tailoring (now surgical, not generic)
if gap_analysis['gaps']:
    prompt = f"The candidate has gaps in {gap_analysis['gaps']}. 
               Find similar experience in the resume and rewrite to bridge these gaps."
    tailored_resume = ai_engine.tailor_resume(resume, job_description, prompt)
```

---

## 📊 Example Output

### Sample Job Description:
```
Requirements:
- 5+ years of Python experience
- Strong knowledge of FastAPI and Django
- Experience with Kubernetes and Docker
- Familiarity with Terraform and Helm
- PostgreSQL database design
```

### Your Resume:
```
Skills: Python, FastAPI, PostgreSQL, Docker

Experience:
- Deployed microservices to Kubernetes clusters
- Built REST APIs with Django
```

### Analysis Result:
```json
{
  "existing": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "supported": ["Kubernetes", "Django"],
  "gaps": ["Terraform", "Helm"]
}
```

### Bot Decision:
```
✅ 4 skills explicitly listed
⚠️ 2 skills supported by experience
❌ 2 skills missing (Terraform, Helm)

Decision: APPLY (6/8 skills covered = 75% match)
```

---

## ⚙️ Configuration

In `config.py`, you can control the behavior:

```python
# Maximum number of skill gaps before auto-skipping
max_skill_gaps = 5

# Minimum percentage of skills that must be "existing" or "supported"
min_skill_coverage = 0.6  # 60%
```

---

## 🚀 Benefits Over Pure LLM Scoring

| Aspect | LLM-Only | With Skill Gap Analysis |
|:---|:---|:---|
| **Precision** | Vague ("good match") | Exact ("missing Terraform, Helm") |
| **Cost** | $0.005 per job | $0 (regex-based) + $0.005 (LLM) |
| **Explainability** | Black box | Transparent buckets |
| **Tailoring Quality** | Generic rewrite | Surgical (targets specific gaps) |
| **False Positives** | High (LLM hallucinates) | Low (deterministic) |

---

## 🧪 Testing the Feature

Run the test script to see it in action:

```bash
python test_skill_analyzer.py
```

Expected output:
```
🔍 Extracting skills from JD...
Found: ['Python', 'FastAPI', 'Kubernetes', 'PostgreSQL', 'Terraform']

📊 Analyzing gaps against resume...
✅ Existing: Python, FastAPI, PostgreSQL
⚠️ Supported: Kubernetes
❌ Gaps: Terraform

Decision: 4/5 skills covered (80%) - APPLY
```

---

## 🔮 Future Enhancements

Potential improvements for the next version:
- **Skill Synonyms:** Recognize that "k8s" = "Kubernetes", "Postgres" = "PostgreSQL".
- **Weighted Gaps:** Mark some skills as "critical" vs "nice-to-have" based on JD language.
- **Learning Mode:** Track which "gaps" you successfully got interviews for, to calibrate the threshold.