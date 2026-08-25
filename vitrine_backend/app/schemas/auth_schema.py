from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str


class DemoStatusResponse(BaseModel):
    """Se este servidor tem modo de demonstração provisionado.

    A landing pública consulta isto para decidir se mostra o botão
    "Ver demo" — numa instalação de cliente real não existe tenant de
    demo, e o botão levaria a um 404.
    """

    disponivel: bool
