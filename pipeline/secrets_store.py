"""Secret Manager access, including persisting a rotated Strava refresh token."""

from google.cloud import secretmanager

from config import PROJECT_ID


class SecretStore:
    def __init__(self, client: secretmanager.SecretManagerServiceClient | None = None) -> None:
        self._client = client or secretmanager.SecretManagerServiceClient()

    def get(self, name: str) -> str:
        path = f"projects/{PROJECT_ID}/secrets/{name}/versions/latest"
        return self._client.access_secret_version(name=path).payload.data.decode()

    def replace(self, name: str, value: str) -> None:
        """Add `value` as the new latest version and destroy all older enabled versions.

        Destroying old versions keeps the secret within the free tier (6 active versions)
        and makes sure a superseded token can't be read back.
        """
        parent = f"projects/{PROJECT_ID}/secrets/{name}"
        new_version = self._client.add_secret_version(
            parent=parent, payload={"data": value.encode()}
        )
        for version in self._client.list_secret_versions(parent=parent, filter="state:ENABLED"):
            if version.name != new_version.name:
                self._client.destroy_secret_version(name=version.name)
