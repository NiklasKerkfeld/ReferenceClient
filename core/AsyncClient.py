import asyncio
import json
import os
import time

import httpx


class AsyncAPIClient:
    def __init__(self, token, model='llama4:latest', server="https://ai-openwebui.gesis.org",
                 timeout=300):
        self.token = token
        self.model = model
        self.server = server
        self.timeout = timeout
        self.cache_file = '../filerefs.json'
        self.files = {}

        # Load cache correctly
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.files = json.load(f)
            except:
                self.files = {}

    def _save_cache(self):
        """Overwrites the cache file with a valid JSON object."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.files, f, ensure_ascii=False, indent=4)

    async def upload_file(self, client: httpx.AsyncClient, file_path: str):
        if file_path in self.files:
            return self.files[file_path]

        url = f'{self.server}/api/v1/files/'
        headers = {'Authorization': f'Bearer {self.token}'}

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = await client.post(url, headers=headers, files=files)

        response.raise_for_status()
        file_id = response.json()['id']

        start_time = time.time()
        while time.time() - start_time < self.timeout:
            status_res = await client.get(
                f'{self.server}/api/v1/files/{file_id}/process/status',
                headers=headers
            )
            if status_res.json().get('status') == 'completed':
                self.files[file_path] = file_id
                self._save_cache()
                return file_id
            await asyncio.sleep(2)

        raise TimeoutError(f"Processing {file_path} timed out")

    async def request_file(self, client: httpx.AsyncClient, file_path: str, message: str):
        file_id = self.files.get(file_path)
        if not file_id:
            raise ValueError(f"File {file_path} not in cache.")

        url = f'{self.server}/api/chat/completions'
        payload = {
            "model": self.model,
            "num_ctx": 64_000,
            "messages": [{"role": "user", "content": message}],
            "files": [{"type": "file", "id": file_id}],
            "rag": {
                "top_k": 100,
                "score_threshold": 0.0,
                "template": "--- BEGIN FILE CONTENT: {{filename}} ---\n{{context}}\n--- END FILE CONTENT ---"
            }
        }

        res = await client.post(url,
                                headers={'Authorization': f'Bearer {self.token}'},
                                json=payload)
        res.raise_for_status()
        return res.json()

