import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class CTraderConfig:
    client_id: str
    client_secret: str
    access_token: str
    account_id: str
    environment: str = "demo"

    # Endpoints
    DEMO_HOST: str = "demo.openapi.ctrader.com"
    LIVE_HOST: str = "live.openapi.ctrader.com"
    PORT: int = 5035

    @property
    def host(self) -> str:
        return self.LIVE_HOST if self.environment.lower() == "live" else self.DEMO_HOST

    @classmethod
    def from_env(cls) -> "CTraderConfig":
        client_id = os.getenv("CTRADER_CLIENT_ID", "")
        client_secret = os.getenv("CTRADER_CLIENT_SECRET", "")
        access_token = os.getenv("CTRADER_ACCESS_TOKEN", "")
        account_id = os.getenv("CTRADER_ACCOUNT_ID", "")
        env = os.getenv("CTRADER_ENVIRONMENT", "demo")

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            account_id=account_id,
            environment=env
        )
