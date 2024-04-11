from newsletter.models import Paper

from langchain.tools import tool


class PaperTools:

    @tool("Query the database")
    def query_database(topic_abbrv: str, limit: int = 10):
        """
        Useful to query the database about a given topic/field abbreviation
        and return relevant results

        Args:
            topic_abbrv (str): The abbreviation of the research topic/field in the database.
            limit (int): the number of papers to extract for the research topic/field

        Returns:
            list: The list containing a dict of paper information.
        """
        papers = Paper.objects.filter(topics__abbrv=topic_abbrv, is_visible=True)[
            :limit
        ]
        papers = [
            {
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "url": paper.get_absolute_url(),
            }
            for paper in papers
        ]

        # OR

        # string = []
        # for paper in papers:
        #     string.append("\n".join([
        #         f"Title: {paper['title']}",
        #         f"Authors: {paper['authors']}",
        #         f"abstract: {paper['abstract']}",
        #         f"url: {paper['url']}",
        #         "\n-------------------"
        #     ]))
        # return "\n".join(string)
        return papers
