from services.llm_client import LLMClient
from config import GOOGLE_API_KEY, GEMINI_API_URL, GEMINI_MODEL

class CandidateEvaluator:
    """Service for evaluating candidates based on job criteria"""
    
    def __init__(self, api_key=None):
        """
        Initialize the candidate evaluator
        
        Args:
            api_key (str, optional): API key for LLM service
        """
        self.api_key = api_key or GOOGLE_API_KEY
    
    def evaluate_candidates(self, job_description, criteria, priorities, resumes):
        """
        Evaluate candidates based on job description, criteria, and priorities
        
        Args:
            job_description (str): The job description text
            criteria (list): List of evaluation criteria
            priorities (dict): Dictionary mapping criteria to priority values (1-10)
            resumes (dict): Dictionary mapping candidate names to resume texts
            
        Returns:
            dict: Evaluation results for each candidate
        """
        results = {}
        
        for candidate, resume_text in resumes.items():
            print(f"Evaluating candidate: {candidate}")
            criteria_scores = self._evaluate_resume(job_description, criteria, resume_text)
            
            # Calculate weighted score
            total_priority = sum(priorities.values())
            weighted_score = 0
            
            for criterion, score in criteria_scores.items():
                criterion_priority = priorities[criterion]
                weighted_score += (score * criterion_priority) / total_priority
            
            # Convert to percentage
            overall_score = (weighted_score / 10) * 100
            
            results[candidate] = {
                'criteria_scores': criteria_scores,
                'overall_score': overall_score
            }
        
        return results
    
    def _evaluate_resume(self, job_description, criteria, resume_text):
        """
        Evaluate a single resume against the criteria using Gemini API
        
        Args:
            job_description (str): The job description text
            criteria (list): List of evaluation criteria
            resume_text (str): The resume text
            
        Returns:
            dict: Scores for each criterion (0-10)
        """
        import requests
        import json
        
        # Truncate resume text if too long to avoid API limits
        max_length = 4000
        if len(resume_text) > max_length:
            resume_text = resume_text[:max_length] + "..."
        
        url = GEMINI_API_URL
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        prompt = f"""
        You are an expert resume screener. Evaluate the following resume against the job description and criteria.
        
        Job Description:
        {job_description}
        
        Resume:
        {resume_text}
        
        Evaluate the candidate on each of the following criteria on a scale of 0-10 (where 10 is perfect match):
        {', '.join(criteria)}
        
        For each criterion, provide:
        1. A score from 0-10
        2. A brief justification (1-2 sentences)
        
        Format your response as:
        Criterion: Score
        Justification: Brief explanation
        
        Repeat for each criterion.
        """
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Parse the response to extract scores
                    scores = {}
                    lines = response_text.strip().split('\n')
                    
                    for criterion in criteria:
                        for i, line in enumerate(lines):
                            if criterion in line and ':' in line:
                                try:
                                    score_text = line.split(':')[1].strip()
                                    # Extract the first number found in the score text
                                    score = next((int(s) for s in score_text.split() if s.isdigit()), 0)
                                    scores[criterion] = min(10, max(0, score))  # Ensure score is between 0-10
                                    break
                                except (ValueError, IndexError):
                                    scores[criterion] = 0
                        
                        # If criterion wasn't found in the response
                        if criterion not in scores:
                            scores[criterion] = 0
                    
                    return scores
            
            # If API call fails, return default scores
            return {criterion: 5 for criterion in criteria}
        except Exception as e:
            print(f"Error evaluating resume: {str(e)}")
            return {criterion: 5 for criterion in criteria}
    
    def generate_feedback(self, job_description, resume_text, criteria_scores):
        """
        Generate detailed feedback for a candidate using Gemini API
        
        Args:
            job_description (str): The job description text
            resume_text (str): The resume text
            criteria_scores (dict): Dictionary of criteria scores
            
        Returns:
            str: Detailed feedback for the candidate
        """
        import requests
        import json
        
        # Truncate texts if too long
        max_length = 2000
        if len(job_description) > max_length:
            job_description = job_description[:max_length] + "..."
        if len(resume_text) > max_length:
            resume_text = resume_text[:max_length] + "..."
        
        # Format criteria scores for the prompt
        criteria_scores_text = "\n".join([f"{criterion}: {score}/10" for criterion, score in criteria_scores.items()])
        
        url = GEMINI_API_URL
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        prompt = f"""
        You are an expert resume reviewer. Generate constructive feedback for a candidate based on their resume and how it matches the job description.
        
        Job Description:
        {job_description}
        
        Resume:
        {resume_text}
        
        Evaluation Scores:
        {criteria_scores_text}
        
        Provide the following feedback:
        1. 3 key strengths of the candidate for this role
        2. 3 areas for improvement or missing qualifications
        3. Overall assessment of fit for the role
        
        Format your response in a professional and constructive manner.
        """
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            return "Unable to generate feedback at this time."
        except Exception as e:
            print(f"Error generating feedback: {str(e)}")
            return "Unable to generate feedback at this time."
