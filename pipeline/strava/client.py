"""Minimal Strava API client: token refresh, activity list, laps."""

import time

import requests

API = "https://www.strava.com/api/v3"
TOKEN_URL = "https://www.strava.com/oauth/token"
PAGE_SIZE = 200
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_ATTEMPTS = 3


class StravaClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self.refresh_token = refresh_token
        self._session = requests.Session()

    def authenticate(self) -> bool:
        """Exchange the refresh token for an access token.

        Returns True when Strava issued a new refresh token, which the caller must persist —
        the old one stops working.
        """
        response = self._request(
            "POST",
            TOKEN_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        payload = response.json()
        self._session.headers["Authorization"] = f"Bearer {payload['access_token']}"
        rotated = payload["refresh_token"] != self.refresh_token
        self.refresh_token = payload["refresh_token"]
        return rotated

    def list_activities(self) -> list[dict]:
        activities: list[dict] = []
        page = 1
        while True:
            batch = self._request(
                "GET",
                f"{API}/athlete/activities",
                params={"per_page": PAGE_SIZE, "page": page},
            ).json()
            if not batch:
                return activities
            activities.extend(batch)
            page += 1

    def list_laps(self, activity_id: str) -> list[dict]:
        return self._request("GET", f"{API}/activities/{activity_id}/laps").json()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = self._session.request(method, url, timeout=30, **kwargs)
            if response.status_code not in RETRYABLE_STATUS or attempt == MAX_ATTEMPTS:
                response.raise_for_status()
                return response
            time.sleep(2**attempt)
        raise AssertionError("unreachable")
