from typing import Any

import requests

from Kael.config import config


class SyncBaseInfo:

    def __init__(self) -> None:
        self.page_size = 100
        self.domain = config.CMDB_DOMAIN
        # Fixed: moved from hardcoded JWT token to environment config
        self.token = config.CMDB_TOKEN

    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def generate_url(self, api_path: str) -> str:
        return f'{self.domain}{api_path}'

    def query_records_total(self, url: str) -> tuple:
        url = self.generate_url(url)
        response = requests.get(url, headers=self.headers(), timeout=30)
        try:
            results = response.json()
            total = results.get('total', 0)
            max_page = int(total / self.page_size) + 1 if total % self.page_size > 0 else int(total / self.page_size)
            page_list = [i for i in range(1, max_page + 1)]
            return total, page_list
        except Exception as err:
            return 0, []
