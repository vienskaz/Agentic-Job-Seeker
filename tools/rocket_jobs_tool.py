from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import requests

from typing import List, Tuple, Optional


class RocketJobsTool:
    """
    Tool responsible for searching and scraping job offers
    from RocketJobs.
    """

    def __init__(self, site_url: str) -> None:
        """
        Initialize tool.

        Args:
            site_url:
                Base URL used for searching jobs.
        """

        self.site_url = site_url

    def search_jobs(self, role_title: str) -> List[str]:
        """
        Search job offers by job title.

        Args:
            role_title:
                Job title to search for.

        Returns:
            List of job offer URLs.
        """

        options = Options()

        options.add_argument(
            "--headless=new"
        )

        options.add_argument(
            "--disable-gpu"
        )

        options.add_argument(
            "--window-size=1920,1080"
        )

        driver = webdriver.Chrome(
            options=options
        )

        url = self._generate_search_url(
            role_title
        )

        try:

            driver.get(url)

            time.sleep(5)

            html = driver.page_source

        finally:

            driver.quit()

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        offers = soup.find_all(
            "a",
            class_="offer-card"
        )

        return [
            offer["href"]
            for offer in offers
            if offer.has_attr("href")
        ]

    def get_job_offer(self, url: str) -> str:
        """
        Download and clean job offer content.

        Args:
            url:
                Job offer URL.

        Returns:
            Clean text content of offer.
        """

        headers = {
            "User-Agent":
            (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64)"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        self._remove_unnecessary_tags(
            soup
        )

        container = self._find_best_container(
            soup
        )

        text = self._extract_text(
            container
        )

        return self._clean_text(
            text
        )

    def _generate_search_url(
            self,
            role_title: str
    ) -> str:

        search_phrase = role_title.replace(
            " ",
            "+"
        )

        search_phrase = search_phrase.lower()

        return (
            f"{self.site_url}"
            f"{search_phrase}"
        )

    def _remove_unnecessary_tags(
            self,
            soup: BeautifulSoup
    ) -> None:

        for tag in soup(
            [
                "script",
                "style",
                "svg",
                "img",
                "picture",
                "source",
                "iframe",
                "noscript",
                "footer",
                "nav",
                "aside",
                "button",
                "form"
            ]
        ):
            tag.decompose()

    def _find_best_container(
            self,
            soup: BeautifulSoup
    ) -> BeautifulSoup:

        candidates: List[
            Tuple[int, BeautifulSoup]
        ] = []

        for tag in soup.find_all(
            [
                "main",
                "article",
                "section",
                "div"
            ]
        ):

            text = tag.get_text(
                " ",
                strip=True
            )

            if len(text) < 500:
                continue

            score = len(text)

            score += (
                len(
                    tag.find_all(
                        [
                            "h1",
                            "h2",
                            "h3"
                        ]
                    )
                )
                * 300
            )

            score += (
                len(
                    tag.find_all("li")
                )
                * 30
            )

            score += (
                len(
                    tag.find_all("p")
                )
                * 50
            )

            score -= (
                len(
                    tag.find_all("a")
                )
                * 15
            )

            score -= (
                len(
                    tag.find_all("button")
                )
                * 50
            )

            candidates.append(
                (
                    score,
                    tag
                )
            )

        if not candidates:
            return soup.body or soup

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return candidates[0][1]

    def _extract_text(
            self,
            container: BeautifulSoup
    ) -> str:

        result = []

        for element in container.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "p",
                "ul",
                "ol"
            ]
        ):

            text = element.get_text(
                " ",
                strip=True
            )

            if not text:
                continue

            if element.name.startswith(
                "h"
            ):

                result.append(
                    f"\n## {text}\n"
                )

            elif element.name in [
                "ul",
                "ol"
            ]:

                for li in element.find_all(
                    "li",
                    recursive=False
                ):

                    li_text = li.get_text(
                        " ",
                        strip=True
                    )

                    if len(li_text) > 3:

                        result.append(
                            f"• {li_text}"
                        )

            else:

                if len(text) > 10:

                    result.append(
                        text
                    )

        return "\n".join(result)

    def _clean_text(
            self,
            text: str
    ) -> str:

        CUT_MARKERS = [
            "Lokalizacja biura",
            "Podobne oferty",
            "Rekomendowane oferty",
            "Polecane oferty",
            "Inne oferty",
            "Zobacz także",
            "Related jobs",
            "Recommended jobs",
            "More jobs",
        ]

        for marker in CUT_MARKERS:

            index = text.lower().find(
                marker.lower()
            )

            if index != -1:

                text = text[:index]

                break

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        text = text.replace(
            "##",
            ""
        )

        lines = []

        previous: Optional[str] = None

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            if line != previous:

                lines.append(
                    line
                )

            previous = line

        return "\n".join(lines)
