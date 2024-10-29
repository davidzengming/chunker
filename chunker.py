import json
from typing import Dict
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


# For testing purpose only, please do not abuse :)
OPEN_AI_API_KEY = "sk-cqf6YlO0yNBw8ibs9P4q0rPkslOGz_R86i6f7UOLivT3BlbkFJIHgnWlHTA2bJN61tLhQ66zVgQEyLrcPMx0-pYa7WIA"
openai_client = OpenAI(api_key=OPEN_AI_API_KEY)

def find_page_soups_from_root(soup) -> Dict[str, BeautifulSoup]:
    """
    Returns a map of children URLs with their soup instance.
    We can parallelize the parsing with some modifications in a distributed env.
    """
    def is_valid_link(link):
        """
        Check if it's a page we want to scrape.
        Set to scrape all pages with path /help but not /help/notion-academy.
        """
        if link.startswith("/help") and not link.startswith("/help/notion-academy/"):
            return True
        
        return False

    def clean_link(link):
        """
        Remove duplicates by looking for #
        """
        section = link.split("#")
        return section[0]

    seen = { '/help' }
    soups = {'/help': soup}
    failed_soups = {}
    level = [soup]
    MAX_SOUPS = 5

    # simple BFS
    while level:
        next_level = []

        for soup in level:
            for link in soup.find_all('a', href=True):
                relative_url = clean_link(link['href'])

                if is_valid_link(relative_url) and relative_url not in seen and (MAX_SOUPS == None or len(soups) < MAX_SOUPS):
                    soup_response = query(NOTION_BASE_URL + relative_url)

                    if soup_response:
                        next_level.append(soup_response)
                    else:
                        failed_soups[relative_url] = soup_response

                    soups[relative_url] = soup_response
                    seen.add(relative_url)
                        

        level = next_level

    return soups

def parse_chunks_from_page(soup_url, soup) -> None:
    """
    Utilize OpenAI GPT-4o-mini model to parse text. LLMs do seem to be really good at this.
    Some other alternatives cossed my mind such as hosting a local LLM on DigitalOcean or something similar, but this is easier.
    """

    prompt = f"""Task: Extract Knowledge Chunks
    
    Please extract knowledge chunks from the following text. 
    Each chunk should capture distinct, self-contained units 
    of information in a subject-description format. Return 
    the extracted knowledge chunks as a JSON object or array, 
    ensuring that each chunk includes both the subject and 
    its corresponding description.
    
    Make sure to keep headers and paragraphs together and don’t break up bulleted lists mid-list. Your chunks should be roughly 750 characters or a bit fewer but could be more if it’s necessary to keep related context together.
    
    Use the format: 
    {{"knowledge_chunks": [
      {{"subject": "subject", "description": "description"}}
    ]}}

    Text:
    {soup}
    """

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": "You are an assistant that takes apart a piece of text into semantic chunks to be used in a RAG system."},
            {"role": "user", "content": prompt},
        ],
        stream=False,
    )
    answer = json.loads(completion.choices[0].message.content)

    print("----- Outputting chunks for url:", soup_url, " -----")
    print("")
    for index, kc in enumerate(answer["knowledge_chunks"]):
        print(index + 1, " - ", kc)
    print("")

def preprocess(soups) -> None:
   # Reduce number of tokens and extract only main body text.
   return {soup_url: soup_val.find('main').get_text() for soup_url, soup_val in soups.items()}

def scrape(url) -> None:
    print("")
    print("")
    print("Querying...")
    all_page_soups = find_page_soups_from_root(query(url))

    processed_soups = preprocess(all_page_soups)
    chunks = {soup_url: parse_chunks_from_page(soup_url, soup_val) for soup_url, soup_val in processed_soups.items()}

    return chunks


def query(url) -> None:
    response = requests.get(url, timeout=5)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        print ("Successfully fetched webpage:", url)
        return soup
    else:
        print("Failed to retrieve webpage:", url)
    return None

NOTION_BASE_URL = "https://www.notion.so"
HELP_URL = "/help"
chunks = scrape(NOTION_BASE_URL + HELP_URL)

