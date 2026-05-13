from pydantic import BaseModel

class EmailContatoCreate(BaseModel):
    email: str
    nome: str

class EmailContatoUpdate(BaseModel):
    email: str
    nome: str

class EmailContatoResponse(BaseModel):
    id: int
    email: str
    nome: str

    model_config = {"from_attributes": True}
