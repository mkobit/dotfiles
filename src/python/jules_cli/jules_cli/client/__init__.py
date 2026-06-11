from jules_cli.client.activity import ActivityClient
from jules_cli.client.session import SessionClient
from jules_cli.client.source import SourceClient


class JulesClient(ActivityClient, SessionClient, SourceClient):
    """
    Client for interacting with the Jules API.
    See: https://developers.google.com/jules/api.
    """
