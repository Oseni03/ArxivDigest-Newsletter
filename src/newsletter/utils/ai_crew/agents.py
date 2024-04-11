from crewai import Agent

from .tools import PaperTools


class AINewsletterAgents:

    def editor_agent(self):
        return Agent(
            role="Editor",
            goal="oversee the creation of the research Newsletter",
            backstory="""With a keen eye for detail and a passion for storytelling,
            you ensure that the newsletter
            not only informs but also engage and inspires the readers.""",
            allow_delegation=True,
            verbose=True,
            max_iter=15,
        )

    def papers_fetcher_agent(self):
        return Agent(
            role="PapersFetcher",
            goal="Query the database for the latest, top papers",
            backstory="""As a database administrator, you will query the database for papers about the given topic/field abbreviation.""",
            tools=[PaperTools.query_database],
            verbose=True,
            allow_delegation=True,
        )

    def papers_analyzer_agent(self):
        return Agent(
            role="NewsAnalyzer",
            goal="Analyze each paper abstract and generate a detailed markdown summary",
            backstory="""With a critical eye and a knack for distilling complex information, you provide insightful 
            analyses of research papers update, making them accessible and angaging for our audience.""",
            tools=[PaperTools.query_database],
            verbose=True,
            allow_delegation=True,
        )

    def newsletter_compiler_agent(self):
        return Agent(
            role="NewsletterCompiler",
            goal="Compile the analyzed papers summary into a final newsletter format",
            backstory="""As the final architect of the newsletter, you acticulosly arrange and
            ensuring a coherent and visually appealing presentation that captivates our reader. Make sure to follow 
            newsletter format guidelines and maintain consistency throughout.""",
            verbose=True,
        )
