import os

from dotenv import load_dotenv

from core.Client import APIClient
import requests

load_dotenv()
TOKEN = os.getenv("TOKEN")


def check_upload():
    path = "data/Literature/DDPM.pdf"

    client = APIClient(TOKEN,
                       model="gpt-oss:120b",
                       server="https://ai-openwebui.gesis.org",
                       timeout=300)

    client.upload_file(path)

    text = client.get_file_text(path)
    print(text)


def check_connection():
    url = 'https://ai-openwebui.gesis.org/api/models'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Models available: {response.text}")


def chat_with_model():
    url = 'https://ai-openwebui.gesis.org/api/chat/completions'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    data = {
        "model": "llama4:latest",
        "messages": [
            {
                "role": "user",
                "content": "Why is the sky blue?"
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"Status: {response.status_code}")
        print(f"Models available: {response.text}")

    response = response.json()
    message = response['choices'][0]['message']['content']
    print(message)


def main():
    client = APIClient(TOKEN,
                       model="gpt-oss:120b",
                       server="https://ai-openwebui.gesis.org",
                       timeout=300)

    response = client.request("Warum sind Bananen krum?")
    message = response['choices'][0]['message']['content']
    print(message)


if __name__ == '__main__':
    check_connection()
