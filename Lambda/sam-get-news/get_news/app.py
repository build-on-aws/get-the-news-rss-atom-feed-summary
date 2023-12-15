import os
import json
from urllib.request import urlopen
import boto3
from botocore.config import Config
import feedparser
from bs4 import BeautifulSoup

BUCKET_NAME = os.environ['OUTPUT_BUCKET']
OBJECT_NAME = os.environ['OUTPUT_FILE']
RSS_LINK = os.environ['RSS_LINK']
SPECIAL_INSTRUCTIONS = os.environ.get('SPECIAL_INSTRUCTIONS', '')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

TEXT_MODEL_ID = 'anthropic.claude-v2'
ACCEPT = 'application/json'
CONTENT_TYPE = 'application/json'

config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)

s3 = boto3.resource('s3')
bedrock = boto3.client("bedrock-runtime", config=config)

summary_prompt_template = '''Write a concise summary (max 200 characters)
    including all the key facts of this article.
    Do not repeat the same concept.
    Ignore header and footer information.
    Just write the summary between the <summary></summary> XML tags with no text before and after.
    {special_instructions}
    <doc>
    {article}
    </doc>
'''

def invoke_text_model(prompt_data):
    if DEBUG:
        print(prompt_data)

    body = json.dumps(
        {
            "prompt": "Human:\n" + prompt_data + "\nAssistant:\n",
            "max_tokens_to_sample": 1000,
            "temperature": 0.8,
            "top_k": 250,
            "top_p": 0.999,
            "stop_sequences": ["Human:"],
            "anthropic_version": "bedrock-2023-05-31",
        }
    )

    response = bedrock.invoke_model(
        body=body, modelId=TEXT_MODEL_ID, accept=ACCEPT, contentType=CONTENT_TYPE
    )
    response_body = json.loads(response.get("body").read())

    outputText = response_body.get("completion")

    if DEBUG:
        print(outputText)

    return outputText


# Create an S3 object from a string
def create_s3_object(bucket_name, object_name, object_content):
    s3.Object(bucket_name, object_name).put(Body=object_content)


def get_text_from_url(url):
    html = urlopen(url).read()
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


def get_delimited_text(text, start_delimeter, end_delimeter, exclude_delimeters=False):
    start_index = text.find(start_delimeter)
    end_index = text.rfind(end_delimeter)
    if exclude_delimeters:
        substring = text[start_index + len(start_delimeter):end_index]
    else:
        substring = text[start_index:end_index + len(end_delimeter)]
    return substring.strip(" \n")


def lambda_handler(event, context):

    d = feedparser.parse(RSS_LINK)

    news = {
        "title": d.feed.title,
        "entries": []
    }

    for entry in d.entries[:10]:  # More recent ten to avoid throttling
        n = {}
        n["title"] = entry["title"]
        n["link"] = entry["link"]
        text = get_text_from_url(n["link"])
        article = n["title"] + "\n\n" + text

        summary = get_delimited_text(
            invoke_text_model(summary_prompt_template.format(
                special_instructions=SPECIAL_INSTRUCTIONS,
                article=article
        )), "<summary>", "</summary>", exclude_delimeters=True)
        
        summary = summary.replace('  ', ' ').replace(' \n', '\n').replace('\n\n\n', '\n\n').strip(' \n') + '\n'

        while True:
            summary = summary.strip()
            if len(summary) <= 240:
                break
            sentences = summary.split(". ")
            sentences.pop()  # Remove last sentence
            if len(sentences) == 0:
                break
            summary = ". ".join(sentences) + "."

        n["summary"] = summary

        news["entries"].append(n)

    json_news = json.dumps(news)

    print(json_news)

    create_s3_object(BUCKET_NAME, OBJECT_NAME, json_news)

    return {
        'statusCode': 200,
        'body': json_news
    }


if __name__ == '__main__':
    # For testing
    lambda_handler({}, {})
