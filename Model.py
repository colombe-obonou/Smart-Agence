from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, MappedAsDataclass
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from typing import List, Optional
from datetime import datetime
import enum


class StatutEnum(enum.Enum):
    en_attente = "En attente"
    en_cours = "En cours" 
    termine = "Terminé"
    annule = "Annulé"


class CategorieEnum(enum.Enum):
    transaction = "transaction"
    conseil = "conseil"


class Base(DeclarativeBase, MappedAsDataclass):
    pass


class Agent(Base):
    __tablename__ = "agent"
    
    
    Nom: Mapped[str] = mapped_column(String(50))
    Prenoms: Mapped[str] = mapped_column(String(50))
    Annee_Naissance: Mapped[int] = mapped_column(Integer)
    Categorie: Mapped[CategorieEnum] = mapped_column(SQLEnum(CategorieEnum), nullable=False)
    Email: Mapped[str] = mapped_column(String(100), unique=True)
    Telephone: Mapped[str] = mapped_column(String(15), unique=True)
    agent_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    Enregistrement_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    
    tickets: Mapped[List["Ticket"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        default_factory=list,
        init=False
    )
    
    events: Mapped[List["Event_ticket"]] = relationship(
        back_populates="agent",
        default_factory=list,
        init=False
    )


class Ticket(Base):
    __tablename__ = "ticket"
    
    
    Categorie_service: Mapped[str] = mapped_column(String(50))
    Description: Mapped[str] = mapped_column(String(500))
    Agent_id: Mapped[int] = mapped_column(ForeignKey("agent.agent_id"))
    Ticket_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    Date_: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    
    agent: Mapped["Agent"] = relationship(
        back_populates="tickets",
        init=False
    )
    
    event_tickets: Mapped[List["Event_ticket"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        default_factory=list,
        init=False
    )


class Event_ticket(Base):
    __tablename__ = "event_ticket"
    

    statut: Mapped[StatutEnum] = mapped_column(SQLEnum(StatutEnum), nullable=False)
    Agent_id: Mapped[int] = mapped_column(ForeignKey("agent.agent_id"), primary_key=True)
    Ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.Ticket_id"), primary_key=True)
    Date_event: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    
   
    agent: Mapped["Agent"] = relationship(
        back_populates="events",
        init=False
    )
    
    ticket: Mapped["Ticket"] = relationship(
        back_populates="event_tickets",
        init=False
    )