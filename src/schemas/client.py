from pydantic import BaseModel, ConfigDict, Field


class ClientInfo(BaseModel):
    """Информация о клиенте (User-Agent, IP)."""

    user_agent: str | None = Field(None, description="User-Agent заголовок")
    ip_address: str | None = Field(None, description="IP адрес клиента")

    model_config = ConfigDict(from_attributes=True)
