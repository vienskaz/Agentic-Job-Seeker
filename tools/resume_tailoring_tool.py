import ollama

from config import config


class ResumeTailoringTool:

    def __init__(self):

        self.client = ollama.Client()
        self.model = config["model"]

    def tailor_resume_to_job(
            self,
            cv: str,
            offer: str
    ) -> str:

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content":
                    """
                    You are an expert technical recruiter, ATS resume optimizer, and hiring manager.

                    Your task is to transform an existing resume so it is specifically optimized
                    for the given job offer.

                    IMPORTANT:
                    The output must be a genuinely tailored resume, not a rewritten copy.

                    Before writing the resume:
                    1. Analyze the job offer.
                    2. Identify:
                    - required skills
                    - technologies
                    - responsibilities
                    - keywords important for ATS systems
                    - expected candidate profile

                    Then modify the resume accordingly.

                    Rules:
                    - Do NOT invent any experience, projects, companies, education, achievements,
                    technologies, certifications, or responsibilities.
                    - Only use information present in the original resume.
                    - Rewrite bullet points to emphasize experience relevant to the job.
                    - Replace generic descriptions with job-specific wording.
                    - Prioritize experience and skills matching the offer.
                    - Move the most relevant skills to the beginning of sections.
                    - Reduce emphasis on unrelated technologies or projects.
                    - Reorder bullet points if needed.
                    - Adapt the professional summary if it exists or create one only using real experience.
                    - Keep measurable achievements when available.

                    For technical roles:
                    - Highlight relevant programming languages, tools, cloud platforms,
                    databases, ML/Data technologies, and engineering practices.
                    - Match terminology used in the job description when truthful.

                    Output:
                    - Return ONLY the final tailored resume.
                    - Do not explain changes.
                    - Do not include analysis.
                    - Do not include comments.
                    """
                },
                {
                    "role": "user",
                    "content":
                    f"""
                    Candidate resume:

                    ----------------
                    {cv}
                    ----------------


                    Job offer:

                    ----------------
                    {offer}
                    ----------------


                    Generate the final ATS-optimized tailored resume.
                    """
                }
            ]
        )

        return response["message"]["content"]
