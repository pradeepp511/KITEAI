from kiteconnect import KiteConnect
from kiteconnect.exceptions import TokenException

from auth.secrets import SecretManager
from auth.settings import settings

secret_manager = SecretManager(project_id=settings.project_id)

api_key = secret_manager.get_secret(secret_id=settings.kite_api_key_secret_id)
api_secret = secret_manager.get_secret(secret_id=settings.kite_api_secret_secret_id)

kite = KiteConnect(api_key=api_key)


def _store_tokens(access_token, refresh_token):
    secret_manager.set_secret(settings.kite_access_token_secret_id, access_token)
    secret_manager.set_secret(settings.kite_refresh_token_secret_id, refresh_token)


def get_access_token() -> str:
    try:
        access_token = secret_manager.get_secret(secret_id=settings.kite_access_token_secret_id)
        kite.set_access_token(access_token)
        kite.profile()  # Check if token is valid
        return access_token
    except (TokenException, Exception):  # Catch Exception for missing secret
        try:
            refresh_token = secret_manager.get_secret(secret_id=settings.kite_refresh_token_secret_id)
            data = kite.renew_access_token(refresh_token, api_secret=api_secret)

            new_access_token = data["access_token"]
            new_refresh_token = data["refresh_token"]

            _store_tokens(new_access_token, new_refresh_token)

            kite.set_access_token(new_access_token)
            return new_access_token
        except Exception as e:
            # This will be hit if the refresh token is invalid or missing.
            raise Exception("Failed to get a valid access token. A manual login might be required.") from e
