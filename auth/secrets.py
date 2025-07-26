from google.cloud import secretmanager


class SecretManager:
    def __init__(self, project_id: str):
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, secret_id: str, version_id: str = "latest") -> str:
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        response = self.client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")

    def set_secret(self, secret_id: str, secret_value: str):
        parent = f"projects/{self.project_id}/secrets/{secret_id}"
        payload = secret_value.encode("UTF-8")
        self.client.add_secret_version(parent=parent, payload={"data": payload})
