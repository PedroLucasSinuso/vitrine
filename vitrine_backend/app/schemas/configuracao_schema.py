from pydantic import BaseModel


class ConfiguracaoResponse(BaseModel):
    configuracoes: dict[str, str]


class ConfiguracaoUpdate(BaseModel):
    valores: dict[str, str]


class LogoUploadResponse(BaseModel):
    logo_url: str