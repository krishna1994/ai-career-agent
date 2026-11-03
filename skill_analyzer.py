import re
from typing import List, Set, Dict, TypedDict

class SkillGapResult(TypedDict):
    existing: List[str]
    supported: List[str]
    gaps: List[str]

class SkillAnalyzer:
    def __init__(self):
        # Ported from career-ops: Headers that open a requirements block
        self.REQUIREMENT_HEADERS = [
            r'required', r'requirements', r'qualifications', r'must[- ]have', 
            r'preferred', r'nice[- ]to[- ]have', r'what\s+we\s+are\s+looking\s+for',
            r'what\s+you\s+will\s+bring', r'who\s+you\s+are', r'about\s+you',
            r'your\s+(?:background|experience|profile)', r'you\s+may\s+be\s+a\s+good\s+fit',
            r'you\s+will\s+have', r'ideal\s+candidate', r'skills\s+(?:and|&)\s+experience'
        ]
        
        # Headers that close a requirements block
        self.NON_REQUIREMENT_HEADERS = [
            r'you\s+will(?!\\s+have)', r'benefits?', r'perks?', r'compensation', 
            r'salary', r'pay\s+range', r'what\s+we\s+offer', r'about\s+us',
            r'interview\s+process', r'how\s+to\s+apply'
        ]
        
        self.BULLET_RE = re.compile(r'^\s*(?:[-*•]|\d{1,2}(?:[.)]\s|[、．）])|[(（]\d{1,2}[)）]|[\u2460-\u2473])\s*(.+)', re.IGNORECASE)
        self.STOPWORDS = {
            'the', 'and', 'for', 'with', 'you', 'your', 'our', 'this', 'that', 'these', 'those',
            'must', 'able', 'ability', 'strong', 'excellent', 'proven', 'a', 'an', 'or', 'in', 'of', 'to', 'as', 'is', 'are',
            'bachelor', 'masters', 'degree', 'diploma', 'certification', 'certificate',
            'experience', 'years', 'year', 'senior', 'junior', 'entry', 'level', 'minimum', 'preferred', 'required',
            'candidates', 'candidate', 'applicants', 'applicant', 'ideal', 'successful',
            'knowledge', 'understanding', 'familiarity', 'exposure', 'background',
            'skills', 'skill', 'communication', 'team', 'teams', 'work', 'working'
        }

    def extract_skills_from_jd(self, jd_text: str) -> List[str]:
        """Extracts potential skill tokens from the requirements section of a JD."""
        lines = jd_text.split('\n')
        extracted_skills = set()
        in_block = False
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line: continue
            
            # Check for block closing
            if any(re.search(h, clean_line, re.I) for h in self.NON_REQUIREMENT_HEADERS):
                in_block = False
                continue
                
            # Check for block opening
            if any(re.search(h, clean_line, re.I) for h in self.REQUIREMENT_HEADERS):
                in_block = True
                continue
            
            if in_block:
                match = self.BULLET_RE.match(line)
                if match:
                    text = match.group(1)
                    # Simple tokenization: split by comma/and, take capitalized words
                    tokens = re.findall(r'\b[A-Z][a-zA-Z0-9+#.]*\b', text)
                    for t in tokens:
                        if t.lower() not in self.STOPWORDS and len(t) > 1:
                            extracted_skills.add(t)
                            
        return list(extracted_skills)

    def analyze_gaps(self, jd_skills: List[str], resume_text: str) -> SkillGapResult:
        """Classifies JD skills into existing, supported, or gaps."""
        # Split resume into "Skills" section and "Prose" (Experience)
        # Simple split based on common "Skills" header
        parts = re.split(r'(?i)##?\s*(?:skills|competencies|technologies)', resume_text)
        
        named_skills = parts[1] if len(parts) > 1 else ""
        prose = parts[0] + ("\n" + parts[2] if len(parts) > 2 else "")
        
        result = {"existing": [], "supported": [], "gaps": []}
        
        for skill in jd_skills:
            # 1. Check if it's in the explicit Skills section
            if re.search(rf'\b{re.escape(skill)}\b', named_skills, re.I):
                result["existing"].append(skill)
            # 2. Check if it's mentioned in the experience prose
            elif re.search(rf'\b{re.escape(skill)}\b', prose, re.I):
                result["supported"].append(skill)
            # 3. Otherwise, it's a gap
            else:
                result["gaps"].append(skill)
                
        return result