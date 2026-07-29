import ollama
from langchain_core.tools import StructuredTool

from config import config


class JobAnalysisTool:

    def __init__(self):

        self.client = ollama.Client()
        self.model = config["model"]

    def analyse_job_fit(
            self,
            cv: str,
            offer: str
    ) -> str:
        """
        Analyse whether candidate matches job offer.

        Compares candidate CV with job requirements.

        Returns:
            Fit analysis with strengths,
            weaknesses and recommendation.
        """

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content":
                    """
                    You are an experienced technical recruiter.

                    Compare candidate CV with job offer.

                    Analyze:
                    - matching skills
                    - missing requirements
                    - experience level
                    - technologies
                    - recommendation

                    Return:
                    1. Match percentage
                    2. Strengths
                    3. Missing skills
                    4. Final recommendation

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

        return response["message"]["content"]
