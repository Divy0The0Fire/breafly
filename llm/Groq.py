from groq import Groq
from os import environ
from dotenv import load_dotenv
import logging

load_dotenv()

SYSTEM = [
    {
        "role": "system",
        "content": f"{open('prompts/System.pp').read()}"
    }
]

client = Groq(api_key=environ['GROQ_API'])

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def Groq(prompt: str = "test", messages: list = [], Print=True):
    try:
        logging.info(f"API request with prompt: {prompt}")
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=SYSTEM + messages + [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096,
            top_p=1,
            stream=True,
            stop=None,
        )
        r = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                r += chunk.choices[0].delta.content
            if Print:
                print(chunk.choices[0].delta.content or "", end="")
        logging.info("API response received successfully")
        return r
    except Exception as e:
        logging.error(f"Error during API request: {e}")
        return None

if __name__ == "__main__":
    while 1:
        Groq(input(">>> "), [])
