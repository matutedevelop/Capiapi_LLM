import httpx
from .config import NEON_DATA_API_URL, TEST_EMAIL, TEST_PASSWORD
from .auth import get_jwt_token

class NeonClient:
    def __init__(self, email: str = None, password: str = None):
        self.email = email or TEST_EMAIL
        self.password = password or TEST_PASSWORD
        self.token = None
        self._authenticate()

    def _authenticate(self):
        self.token = get_jwt_token(self.email, self.password)

    def _get_headers(self, extra: dict = None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def _request(self, method: str, table: str, extra_headers: dict = None, **kwargs):
        r = httpx.request(
            method,
            f"{NEON_DATA_API_URL}/{table}",
            headers=self._get_headers(extra_headers),
            **kwargs
        )
        if r.status_code == 401:
            print("Token expired, re-authenticating...")
            self._authenticate()
            r = httpx.request(
                method,
                f"{NEON_DATA_API_URL}/{table}",
                headers=self._get_headers(extra_headers),
                **kwargs
            )
        return r

    def select(self, table: str, params: dict = None):
        r = self._request("GET", table, params=params)
        print(f"SELECT {table} - status: {r.status_code}")
        return r.json()

    def insert(self, table: str, data: dict):
        r = self._request(
            "POST", table,
            extra_headers={"Prefer": "return=representation"},
            json=data
        )
        print(f"INSERT {table} - status: {r.status_code}")
        if r.status_code in (200, 201) and r.content:
            result = r.json()
            if isinstance(result, list):
                return result[0] if result else {}
            return result
        else:
            print(f"INSERT {table} ended with code {r.status_code} log:\n  {r.text}")
            return {}

    def update(self, table: str, params: dict, data: dict):
        r = self._request("PATCH", table, params=params, json=data)
        print(f"UPDATE {table} - status: {r.status_code}")
        return r.json()

    def delete(self, table: str, params: dict):
        r = self._request("DELETE", table, params=params)
        print(f"DELETE {table} - status: {r.status_code}")
        return r.status_code
