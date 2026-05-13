from pydantic import BaseModel

class WhatsAppContatoCreate(BaseModel):
    numero: str
    nome: str

class WhatsAppContatoResponse(BaseModel):
    id: int
    numero: str
    nome: str

    model_config = {"from_attributes": True}

class WhatsAppContatoUpdate(BaseModel):
    numero: str
    nome: str
