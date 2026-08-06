from pypdf import PdfReader
import re
from config import config
import time
import json


class ResumeHandlerTool:
    """
    Handles resume processing tasks:
    - reading PDF resumes,
    - cleaning extracted text.
    """

    def __init__(self):
        """
        Initializes ResumeHandler using application configuration.
        """

        self.file_path = config["resume_file_path"]
        self.cached_resume = None
        self.cache_timestamp = None
        self.cache_ttl = 3600

    def read_resume(self) -> str:
        """
        Reads text content from user's PDF resume.

        Returns:
            Extracted raw resume text.
        """

        reader = PdfReader(
            self.file_path
        )

        raw_resume = ""

        for page in reader.pages:

            text = page.extract_text()

            if text:
                raw_resume += text + "\n"

        return raw_resume

    def clean_cv_text(self, text: str) -> str:
        """
        Cleans extracted resume text.
        """

        text = text.replace(
            "\x00",
            " "
        )

        text = re.sub(
            r"-\n",
            "",
            text
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        text = re.sub(
            r"(?<!\n)\n(?!\n)",
            " ",
            text
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        return text.strip()

    def get_resume(self):

        if self.cached_resume and self.cache_timestamp:
            if time.time() - self.cache_timestamp < self.cache_ttl:
                return self.cached_resume

        raw_resume = self.read_resume()
        self.cached_resume = self.clean_cv_text(raw_resume)
        self.cache_timestamp = time.time()

        return self.cached_resume
