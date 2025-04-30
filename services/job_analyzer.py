from services.llm_client import LLMClient
from config import GOOGLE_API_KEY, GEMINI_API_URL, GEMINI_MODEL

class JobAnalyzer:
    """Service for analyzing job descriptions and generating evaluation criteria"""
    
    def __init__(self, api_key=None):
        """
        Initialize the job analyzer
        
        Args:
            api_key (str, optional): API key for LLM service
        """
        self.api_key = api_key or GOOGLE_API_KEY
    
    def generate_criteria(self, job_description):
        """
        Analyze job description and generate evaluation criteria
        
        Args:
            job_description (str): The job description text
            
        Returns:
            list: List of criteria for evaluating candidates
        """
        try:
            response = self._call_gemini_api(job_description)
            
            # Process the response to get a clean list of criteria
            criteria_text = response.strip()
            criteria_list = [line.strip() for line in criteria_text.split('\n') if line.strip()]
            
            # Filter out any lines that are too long or look like explanations
            criteria_list = [c for c in criteria_list if len(c) < 50 and '.' not in c]
            
            # Limit to 8 criteria maximum
            return criteria_list[:8]
        except Exception as e:
            print(f"Error generating criteria: {str(e)}")
            # Return default criteria if API call fails
            return ["Technical Skills", "Experience", "Education", "Communication Skills", "Problem Solving"]
    
    def _call_gemini_api(self, job_description):
        """
        Call Gemini API to analyze job description
        
        Args:
            job_description (str): The job description text
            
        Returns:
            str: The generated criteria text
        """
        import requests
        import json
        
        url = GEMINI_API_URL
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        prompt = f"""
        Based on the following job description, identify 5-8 key evaluation criteria that would be important for 
        screening candidates. These should be specific, measurable aspects that can be evaluated from a resume.
        
        Job Description:
        {job_description}
        
        Format your response as a simple list of criteria, one per line, without numbering or bullet points.
        For example:
        Technical Skills
        Years of Experience
        Education Level
        Industry Knowledge
        Project Management Experience
        """
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, params=params, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            return ""
        else:
            raise Exception(f"API returned status code {response.status_code}: {response.text}")
    
    def analyze_job_requirements(self, job_description):
        """
        Analyze job description to extract key requirements
        
        Args:
            job_description (str): The job description text
            
        Returns:
            dict: Dictionary of key requirements categories
        """
        try:
            import requests
            import json
            
            url = GEMINI_API_URL
            
            headers = {
                "Content-Type": "application/json"
            }
            
            params = {
                "key": self.api_key
            }
            
            prompt = f"""
            Analyze the following job description and extract key requirements in these categories:
            1. Technical Skills
            2. Experience Level
            3. Education Requirements
            4. Industry Knowledge
            
            Job Description:
            {job_description}
            
            Format your response as:
            Technical Skills: [list skills separated by commas]
            Experience Level: [experience level]
            Education Requirements: [education requirements]
            Industry Knowledge: [industry knowledge areas]
            """
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, params=params, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Parse the response into a dictionary
                    requirements = {}
                    current_category = None
                    
                    for line in response_text.strip().split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                            
                        if ':' in line:
                            parts = line.split(':', 1)
                            category = parts[0].strip()
                            value = parts[1].strip()
                            requirements[category] = value
                    
                    return requirements
                return {}
            else:
                raise Exception(f"API returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error analyzing job requirements: {str(e)}")
            return {
                "Technical Skills": "Not available",
                "Experience Level": "Not available",
                "Education Requirements": "Not available",
                "Industry Knowledge": "Not available"
            }
