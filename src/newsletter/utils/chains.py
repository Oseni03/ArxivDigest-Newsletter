from django.conf import settings

from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain.output_parsers import CommaSeparatedListOutputParser


GeminiLLM = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=settings.GOOGLE_API_KEY)


def summarizer(text: str):
    with open("./prompts/summarize.txt", "r") as file:
        prompt_template = file.read()
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

    chain = load_summarize_chain(GeminiLLM, chain_type="stuff", prompt=prompt, verbose=True)
    return chain.run(text)


def bullet_summarizer(texts):
    output_parser = CommaSeparatedListOutputParser()

    with open("./prompts/bullet_summarize.txt", "r") as file:
        prompt_template = file.read()

    format_instructions = output_parser.get_format_instructions()

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["texts"],
        partial_variables={"format_instructions": format_instructions}
    )
    
    chain = load_summarize_chain(GeminiLLM, chain_type="stuff", prompt=prompt, verbose=True)
    
    # _input = prompt.format(texts=texts)
    output = chain.run(texts)
    return output_parser.parse(output)