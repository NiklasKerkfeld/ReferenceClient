import json
import os
import time

import requests
from requests import HTTPError


class FileUploadError(Exception):
    """Exception raised for errors during the file upload process."""

    def __init__(self, message):
        super().__init__(f"Failed during upload: {message}")



class APIClient:
    def __init__(self,
                 token: str,
                 model: str = 'llama4:latest',
                 server: str = "https://ai-openwebui.gesis.org",
                 timeout: int = 300):

        self.token = token
        self.model = model
        self.server = server
        self.timeout: int = timeout
        self.cache_file = 'filerefs.json'
        self.files = {}

        # Load cache correctly
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.files = json.load(f)
            except:
                print(f"could not load cached file: {self.cache_file}")
                self.files = {}


    def _save_cache(self):
        """Overwrites the cache file with a valid JSON object."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.files, f, ensure_ascii=False, indent=4)

    def request(self, message: str):
        url = f'{self.server}/api/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": self.model,
            "num_ctx": 64_000,
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            raise HTTPError(f"Error: {response.status_code}")

        return response.json()

    def upload_file(self, file_path: str):
        if file_path in self.files.keys():
            print(f"file already uploaded: {self.files[file_path]}")
            return self.files[file_path]

        with open(file_path, 'rb') as file:
            url = f'{self.server}/api/v1/files/'
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/json'
            }

            files = {'file': file}
            response = requests.post(url, headers=headers, files=files, timeout=120)

        if response.status_code != 200:
            raise HTTPError(f"Error: {response.status_code}")

        response = response.json()
        file_id = response['id']
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            status_response = requests.get(
                f'{self.server}/api/v1/files/{file_id}/process/status',
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                }
            )

            status_data = status_response.json()
            status = status_data.get('status')

            if status == 'completed':
                self.files[file_path] = file_id
                self._save_cache()
                return file_id

            elif status == 'failed':
                raise FileUploadError(f"Upload failed")

            time.sleep(2)
        else:
            raise TimeoutError("File processing timed out")

    def get_file_text(self, file_path: str):
        file_id = self.files[file_path]

        response = requests.get(
            f'{self.server}/api/v1/files/{file_id}/content',
            headers={
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            })

        if response.status_code != 200:
            raise Exception(f"Failed to get text: {response.status_code} - {response.text}")

        print(type(response))
        print(response)

        return response.text

    def request_file(self, file_path: str, message: str):
        file_id = self.files[file_path]
        url = f'{self.server}/api/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "model": self.model,
            "num_ctx": 64_000,
            "messages": [{"role": "user", "content": message}],
            "files": [{"type": "file", "id": file_id}],
            "temperature": 0.0,
            "rag": {
                "top_k": 100,
                "score_threshold": 0.0,
                "num_results": 100,
                "reranking_model": "bge-reranker-v2-m3",
                "template": "--- BEGIN FILE CONTENT: {{filename}} ---\n{{context}}\n--- END FILE CONTENT ---"
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise HTTPError(f"Error: {response.status_code}")

        return response.json()
