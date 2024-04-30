from modal import Image, App, Stub, wsgi_app

app = App()
stub = Stub()
image = Image.debian_slim().pip_install(
    "flask==3.0.3",
    "langchain==0.1.14",
    "langchain_openai==0.0.5",
    "python-dotenv==1.0.0",
    "langchainhub==0.1.15",
    "requests"
)

@app.function(image=image)
@wsgi_app()
def flask_app():
    from langchain.prompts import PromptTemplate
    from langchain.chains.summarize import load_summarize_chain
    from langchain_community.document_loaders import TextLoader
    from langchain_openai import OpenAI, ChatOpenAI

    from dotenv import load_dotenv
    from time import time

    from flask import Flask, request
    import zipfile
    import requests
    import re

    web_app = Flask(__name__)

    @web_app.get("/summarize")
    def sum():
        url = "https://github.com/hasnainali659/Testing/raw/main/inputDoc.zip"
        response = requests.get(url)

        with open("inputDoc.zip", 'wb') as f:
            f.write(response.content)
        
        with zipfile.ZipFile("inputDoc.zip", "r") as zip_ref:
            zip_ref.extractall()
            
        loader = TextLoader("inputDoc/case.txt")
        pages = loader.load()
        
        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.3, openai_api_key="")
        prompt_template = """
        Summarize the text below:
        {text}
        
        Provide a detailed summary of the text above.
        
        Detailed Summary:
        
        Also, provide important part summary in the format below:
        
        Example:
        
        Page Line: 10-15
        Topic: Introduction
        Summary: This section introduces the topic of the document.
        """
        
        summary_prompt = PromptTemplate(
            template=prompt_template, input_variables=["text"]
        )

        summarize_chain = load_summarize_chain(
            llm=llm, chain_type="stuff", prompt=summary_prompt
        )

        result = summarize_chain.invoke(pages)
        text = result["output_text"]

        detailed_summary_pattern = r"Detailed Summary:(.*?)Important Part Summary:"
        important_summary_pattern = r"Important Part Summary:(.*?)$"

        detailed_summary_match = re.search(detailed_summary_pattern, text, re.DOTALL)
        important_summary_match = re.search(important_summary_pattern, text, re.DOTALL)

        detailed_summary = (
            detailed_summary_match.group(1).strip() if detailed_summary_match else ""
        )
        important_summary = (
            important_summary_match.group(1).strip() if important_summary_match else ""
        )

        summary_details = []
        pattern = r"Page Line: (\d+-\d+)\nTopic: (.*?)\nSummary: (.*?)\n\n"
        summary_text = important_summary
        matches = re.findall(pattern, summary_text)

        for match in matches:
            page_line = match[0]
            topic = match[1]
            summary = match[2]
            summary_details.append(
                {"page_line": page_line, "topic": topic, "summary": summary}
            )

        important_summary_details = summary_details

        result_json = {
            "detailed_summary": detailed_summary,
            "important_summary": important_summary_details,
        }
        
        return result_json

    return web_app