from django.conf import settings

from crewai import Crew, Process

from .agents import AINewsletterAgents
from .tasks import AINewsletterTasks
from .database_io import save_markdown
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_openai import ChatOpenAI

# OpenAIGPT4 = ChatOpenAI(
#     model="gpt-4"
# )
#

GeminiLLM = ChatGoogleGenerativeAI(
    model="gemini-pro", google_api_key=settings.GOOGLE_API_KEY
)


agents = AINewsletterAgents()
tasks = AINewsletterTasks()

# Setting up agents
editor = agents.editor_agent()
news_fetcher = agents.papers_fetcher_agent()
news_analyzer = agents.papers_analyzer_agent()
newsletter_compiler = agents.newsletter_compiler_agent()

# Setting up tasks
fetch_papers_task = tasks.fetch_papers_task(news_fetcher)
analyzed_news_task = tasks.analyze_papers_task(news_analyzer, [fetch_papers_task])
compile_newsletter_task = tasks.compile_newsletter_task(
    newsletter_compiler, [analyzed_news_task], save_markdown
)

# Setting up tools
crew = Crew(
    agents=[editor, news_fetcher, news_analyzer, newsletter_compiler],
    tasks=[fetch_papers_task, analyzed_news_task, compile_newsletter_task],
    process=Process.hierarchical,
    manager_llm=GeminiLLM,
)


# Kick start the Crew
result = crew.kickoff()

print(result)
