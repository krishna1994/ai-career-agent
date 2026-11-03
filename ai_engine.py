import os
import config
import utils
import json
import requests
from local_ai_provider import LocalAIProvider

class AIEngine:
    def __init__(self):
        self.api_key = config.ai_api_key
        self.model = config.ai_model
        self.enabled = config.use_ai_features
        
        # Initialize Local AI as fallback provider
        self.local_ai = LocalAIProvider()
        
        # Determine active provider
        if self.api_key and self.api_key != "YOUR_API_KEY_HERE" and self.api_key.startswith("sk-"):
            self.provider = "OPENAI"
        else:
            self.provider = "LOCAL_AI"
            if self.enabled:
                utils.prYellow("ℹ️ No OpenAI key found. Using Local AI as AI provider.")

    def _call_llm(self, system_prompt, user_prompt):
        if not self.enabled:
            return None
        
        if self.api_key == "YOUR_API_KEY_HERE":
            utils.prRed("❌ AI API Key not configured in config.py")
            return None

        try:
            # This implementation assumes OpenAI-compatible API
            # For Anthropic, the payload structure would differ slightly
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            utils.prYellow(f"⚠️ AI Engine Error: {str(e)}")
            return None

    def get_ats_score(self, resume_text, job_description):
        """Scores the fit between resume and JD from 1 to 5."""
        # Use Local AI if it's the active provider
        if self.provider == "LOCAL_AI":
            return self.local_ai.get_ats_score(resume_text, job_description)
        
        # OpenAI implementation
        system_prompt = "You are an expert ATS (Applicant Tracking System) and Recruiter. Score the candidate's fit for the job from 1 to 5. Return ONLY a JSON object: {\"score\": int, \"reason\": \"string\"}"
        user_prompt = f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}"
        
        result = self._call_llm(system_prompt, user_prompt)
        if result:
            try:
                return json.loads(result)
            except:
                return {"score": 1, "reason": "Error parsing AI response"}
        return {"score": 1, "reason": "AI unavailable"}

    def tailor_resume(self, resume_text, job_description):
        """Tailors the resume bullet points to match the job description."""
        # Use Local AI if it's the active provider
        if self.provider == "LOCAL_AI":
            return self.local_ai.tailor_resume(resume_text, job_description)
        
        # OpenAI implementation
        system_prompt = "You are a professional resume writer. Rewrite the experience section of the resume to better align with the job description. Maintain honesty but emphasize relevant skills. Return the full updated resume text."
        user_prompt = f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}"
        
        return self._call_llm(system_prompt, user_prompt)

    def answer_question(self, resume_text, job_description, question):
        """Generates a tailored answer to a specific application question."""
        # Use Local AI if it's the active provider
        if self.provider == "LOCAL_AI":
            return self.local_ai.answer_question(resume_text, job_description, question)
        
        # OpenAI implementation
        system_prompt = "You are a job applicant. Answer the following application question based on the provided resume and job description. Keep the answer concise, professional, and truthful."
        user_prompt = f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}\n\nQuestion: {question}"
        
        return self._call_llm(system_prompt, user_prompt)
