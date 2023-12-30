from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser


output_parser = CommaSeparatedListOutputParser()


def summarize(paper_abstracts):
    """
    Args:
        papers_contents: a list of str
    """
    
    template = """Given the list of research paper abstract, please provide a concise summary highlighting the most insightful points and key findings in one sentence for each of the abstract.

    {abstracts}
    
    {format_instructions}"""
    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template=template,
        input_variables=["abstracts"],
        partial_variables={"format_instructions": format_instructions}
    )
    
    model = OpenAI(temperature=0)
    
    _input = prompt.format(abstracts=paper_abstracts)
    output = model(_input)
    return output_parser.parse(output)
