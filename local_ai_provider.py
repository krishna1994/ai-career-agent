"""
local_ai_provider.py - Local AI Proxy Integration
Provides an AI interface by communicating with a local AI proxy.
"""

import requests
import json
import utils
from typing import Dict, Any, Optional

class LocalAIProvider:
    def __init__(self):
        # The Local AI proxy typically runs on localhost
        # Default port for Local AI proxy is usually 8080
        self.api_url = "http://localhost:8080/chat" 
        self.timeout = 60

    def _call_local_ai(self, prompt: str) -> Optional[str]:
        """Sends a prompt to the local AI proxy."""
        try:
            # The MCP proxy expects a JSON payload with the prompt
            payload = {
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            # Handle different possible response formats from the proxy
            if "content" in result:
                return result["content"]
            elif "response" in result:
                return result["response"]
            elif "choices" in result:
                return result["choices"][0]["message"]["content"]
            
            return str(result)
        except Exception as e:
            utils.prYellow(f"⚠️ Local AI Proxy Error: {str(e)}")
            return None

    def get_ats_score(self, resume: str, jd: str) -> Dict[str, Any]:
        """Scores a resume against a JD using Local AI."""
        prompt = (
            f"You are an expert ATS (Applicant Tracking System). "
            f"Score the following resume against the job description on a scale of 1-5.\n\n"
            f"RESUME:\n{resume}\n\n"
            f"JOB DESCRIPTION:\n{jd}\n\n"
            f"Return ONLY a JSON object with keys 'score' (integer 1-5) and 'reason' (short explanation)."
        )
        
        response = self._call_local_ai(prompt)
        if not response:
            return {"score": 1, "reason": "Local AI Proxy unavailable"}

        try:
            # Extract JSON from response
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"score": 1, "reason": "Invalid response format from Local AI"}
        except Exception as e:
            return {"score": 1, "reason": f"Parsing error: {str(e)}"}

    def answer_question(self, resume: str, jd: str, question: str) -> str:
        """Answers a specific application question using Local AI."""
        prompt = (
            f"Based on the following resume and job description, provide a professional, "
            f"truthful, and concise answer to the application question.\n\n"
            f"RESUME:\n{resume}\n\n"
            f"JOB DESCRIPTION:\n{jd}\n\n"
            f"QUESTION: {question}\n\n"
            f"Answer directly and professionally."
        )
        
        response = self._call_local_ai(prompt)
        return response if response else "I'm sorry, I couldn't generate an answer at this time."

    def tailor_resume(self, resume: str, jd: str) -> str:
        """Tailors the resume for a specific JD using Local AI."""
        prompt = (
            f"You are a professional resume writer. Rewrite the following resume to better "
            f"align with the job description. Focus on highlighting relevant skills and "
            f"quantifying achievements. Keep the original facts but optimize the wording.\n\n"
            f"RESUME:\n{resume}\n\n"
            f"JOB DESCRIPTION:\n{jd}\n\n"
            f"Return the full rewritten resume."
        )
        
        response = self._call_local_ai(prompt)
        return response if response else resume