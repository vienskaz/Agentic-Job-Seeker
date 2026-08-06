import ollama
import json

from config import config


class ResumeTailoringTool:

    def __init__(self):

        self.client = ollama.Client()
        self.model = config["model"]

    def tailor_resume_to_job(
            self,
            cv: str,
            offer: str
    ) -> dict:

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content":
                    """
                    You are an experienced technical recruiter.

                    

                    Tailor candidate's CV to the job vacancy so that it’s a better fit, 
                    but don’t make up experience – take everything that’s in 
                    candidate's CV and phrase it more effectively.
                    
                    """
                },
                {
                    "role": "user",
                    "content":
                    f"""
                    Candidate CV:

                    {cv}


                    Job offer:

                    {offer}
                    """
                }
            ]
        )

        content = response["message"]["content"]

        return json.loads(
            content
        )
