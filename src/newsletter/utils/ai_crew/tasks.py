from crewai import Task 
from datetime import datetime


class AINewsletterTasks:

    def fetch_papers_task(self, agent):
        return Task(
            description=f"Fetch most recent research papers from the database. The current time is {datetime.now()}.",
            agent=agent,
            async_execution=True,
            expected_output="""A list of most recent research papers titles, urls, and a brief summay for each story from the paper abstract
                Example Output:
                [
                    {
                        "title": "AI takes spotlight in Super Bowl commercials",
                        "url": "https://example.com/story1",
                        "summary": "AI made a splash in this year\'s Super Bowl commercials..."
                    },
                    {{...}}
                ]"""
        )
    
    def analyze_papers_task(self, agent, context):
        return Task(
            description="Analyze each research paper and ensure there are at least 5 well-formatted points",
            agent=agent,
            async_execution=True,
            context=context,
            expected_output="""A markdown-formatted analysis for each news story, including a rundown, detailed bull
                and a "why it matters" section. There should be at least 5 articles, each following the proper format.
                Example Output:
                "## AI takes spotlight in Super Bowl commercials\n\n
                **The Rundown:**
                ** AI made a splash in this year\'s SUper Bowl commercials...\n\n
                **The details:**\n\n
                - Microsoft\'s Copilot spot showcased its AI assistant...\n\n
                **Why it matters:** While AI-related ads have been rampant over the last year, its SUper Bowl presents...
            """
        )
    
    def compile_newsletter_task(self, agent, context, callback_function):
        return Task(
            description="Compile the newsletter",
            agent=agent,
            context=context,
            expected_output="""A complete newsletter in markdown format, with a consistent style and layout,
                Example Output:
                "# Top stories in AI today:\\n\\n
                - AI takes spotlight in Super Bowl commercials\\n
                - Altman seeks TRILLIONS for global AI chip initiative\\n\\n

                ## AI takes spotligt in Super Bowl commercials\\n\\n
                **The Rundown:** AI made a splash in this year\'s Super Bowl commercials...\\n\\n
                **The details:**...\\n\\n
                **Why it matters:**...\\n\\n
                ## Altman seeks TRILLIONS for global AI chip initiative\\n\\n
                **The Rundown:** OpenAI CEO Sam Altman is reportedly angling to raise TRILLIONS of dollars...\\n\\n"
                **The details:**...\\n\\n
                **Why it matters:**...\\n\\n
            """,
            callback=callback_function
        )