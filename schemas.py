from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum



class StatutEnum(str, Enum):
    en_attente = "En attente"
    en_cours = "En cours"
    termine = "Terminé"
    annule = "Annulé"


class CategorieEnum(str, Enum):
    transaction = "transaction"
    conseil = "conseil"


# Schemas pour Agent
class AgentBase(BaseModel):
    Nom: str = Field(..., min_length=2, max_length=50)
    Prenoms: str = Field(..., min_length=2, max_length=50)
    Annee_Naissance: int = Field(..., ge=1940, le=2010)
    Categorie: CategorieEnum
    Email: EmailStr
    Telephone: str = Field(..., pattern=r'^\+?[\d\s\-\(\)]{8,15}$')
    
    @field_validator('Annee_Naissance')
    @classmethod
    def validate_age(cls, v):
        current_year = datetime.now().year
        age = current_year - v
        if age < 18 or age > 80:
            raise ValueError('L\'âge doit être entre 18 et 80 ans')
        return v


class AgentCreate(AgentBase):
    Enregistrement_date: Optional[datetime] = Field(default_factory=datetime.now)


class AgentUpdate(BaseModel):
    Nom: Optional[str] = Field(None, min_length=2, max_length=50)
    Prenoms: Optional[str] = Field(None, min_length=2, max_length=50)
    Annee_Naissance: Optional[int] = Field(None, ge=1940, le=2010)
    Categorie: Optional[CategorieEnum] = None
    Email: Optional[EmailStr] = None
    Telephone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]{8,15}$')
    
    @field_validator('Annee_Naissance')
    @classmethod
    def validate_age(cls, v):
        if v is not None:
            current_year = datetime.now().year
            age = current_year - v
            if age < 18 or age > 80:
                raise ValueError('L\'âge doit être entre 18 et 80 ans')
        return v


class Agent(AgentBase):
    agent_id: int
    Enregistrement_date: datetime
    
    model_config = {
        "from_attributes": True,
        "use_enum_values": True
    }


# Schemas pour Ticket
class TicketBase(BaseModel):
    Categorie_service: str = Field(..., min_length=3, max_length=50)
    Description: str = Field(..., min_length=10, max_length=500)


class TicketCreate(TicketBase):
    Agent_id: int
    Date_: Optional[datetime] = Field(default_factory=datetime.now)


class TicketUpdate(BaseModel):
    Categorie_service: Optional[str] = Field(None, min_length=3, max_length=50)
    Description: Optional[str] = Field(None, min_length=10, max_length=500)
    Agent_id: Optional[int] = None


class Ticket(TicketBase):
    Ticket_id: int
    Date_: datetime
    Agent_id: int
    
    model_config = {
        "from_attributes": True
    }


# Schemas pour Event_ticket
class EventTicketBase(BaseModel):
    statut: StatutEnum
    Date_event: Optional[datetime] = Field(default_factory=datetime.now)


class EventTicketCreate(EventTicketBase):
    Agent_id: int
    Ticket_id: int


class EventTicketUpdate(BaseModel):
    statut: Optional[StatutEnum] = None


class EventTicket(EventTicketBase):
    Agent_id: int
    Ticket_id: int
    Date_event: datetime
    
    model_config = {
        "from_attributes": True,
        "use_enum_values": True
    }



class AgentWithTickets(Agent):
    tickets: List[Ticket] = []


class TicketWithEvents(Ticket):
    event_tickets: List[EventTicket] = []
    agent: Optional[Agent] = None