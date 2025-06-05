from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime, date

import Model, schemas


#CRUD AGENTS

def create_agent(db: Session, agent: schemas.AgentCreate) -> Model.Agent:
    """Créer un nouvel agent"""
    db_agent = Model.Agent(
        Nom=agent.Nom,
        Prenoms=agent.Prenoms,
        Annee_Naissance=agent.Annee_Naissance,
        Categorie=agent.Categorie,
        Enregistrement_date=agent.Enregistrement_date or datetime.now(),
        Email=agent.Email,
        Telephone=agent.Telephone
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_id: int) -> Optional[Model.Agent]:
    """Récupérer un agent par son ID"""
    return db.query(Model.Agent).filter(Model.Agent.agent_id == agent_id).first()


def get_agent_by_email(db: Session, email: str) -> Optional[Model.Agent]:
    """Récupérer un agent par son email"""
    return db.query(Model.Agent).filter(Model.Agent.Email == email).first()


def get_agents(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    categorie: Optional[str] = None,
    search: Optional[str] = None
) -> List[Model.Agent]:
    """Récupérer la liste des agents avec filtres optionnels"""
    query = db.query(Model.Agent)
    
    # Filtrer par catégorie
    if categorie:
        query = query.filter(Model.Agent.Categorie == categorie)
    
    # Recherche dans nom/prénoms
    if search:
        search_filter = or_(
            Model.Agent.Nom.ilike(f"%{search}%"),
            Model.Agent.Prenoms.ilike(f"%{search}%"),
            Model.Agent.Email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    return query.offset(skip).limit(limit).all()


def update_agent(db: Session, agent_id: int, agent_update: schemas.AgentUpdate) -> Optional[Model.Agent]:
    """Mettre à jour un agent"""
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return None
    
    update_data = agent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_agent, field, value)
    
    db.commit()
    db.refresh(db_agent)
    return db_agent


def delete_agent(db: Session, agent_id: int) -> bool:
    """Supprimer un agent"""
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return False
    
    db.delete(db_agent)
    db.commit()
    return True


def get_agent_statistics(db: Session, agent_id: int) -> dict:
    """Récupérer les statistiques d'un agent"""
    agent = get_agent(db, agent_id)
    if not agent:
        return {}
    
    total_tickets = db.query(Model.Ticket).filter(Model.Ticket.Agent_id == agent_id).count()
    
    # Statistiques par statut
    tickets_stats = {}
    for statut in Model.StatutEnum:
        count = db.query(Model.Event_ticket).filter(
            and_(
                Model.Event_ticket.Agent_id == agent_id,
                Model.Event_ticket.statut == statut
            )
        ).count()
        tickets_stats[statut.value] = count
    
    return {
        "agent_id": agent_id,
        "nom_complet": f"{agent.Prenoms} {agent.Nom}",
        "total_tickets": total_tickets,
        "tickets_par_statut": tickets_stats
    }


#CRUD TICKETS

def create_ticket(db: Session, ticket: schemas.TicketCreate) -> Model.Ticket:
    """Créer un nouveau ticket"""
    # Vérifier que l'agent existe
    agent = get_agent(db, ticket.Agent_id)
    if not agent:
        raise ValueError(f"Agent avec ID {ticket.Agent_id} n'existe pas")
    
    db_ticket = Model.Ticket(
        Date_=ticket.Date_ or datetime.now(),
        Categorie_service=ticket.Categorie_service,
        Description=ticket.Description,
        Agent_id=ticket.Agent_id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    # Dans cette partie nous avons la création de  l'événement initial "en_attente"
    create_ticket_event(
        db, 
        ticket.Agent_id, 
        db_ticket.Ticket_id, 
        Model.StatutEnum.en_attente
    )
    
    return db_ticket


def get_ticket(db: Session, ticket_id: int) -> Optional[Model.Ticket]:
    """Récupérer un ticket par son ID"""
    return db.query(Model.Ticket).filter(Model.Ticket.Ticket_id == ticket_id).first()


def get_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    categorie: Optional[str] = None,
    agent_id: Optional[int] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    statut: Optional[str] = None
) -> List[Model.Ticket]:
    """Récupérer la liste des tickets avec filtres"""
    query = db.query(Model.Ticket)
    
    # Filtrer par catégorie de service
    if categorie:
        query = query.filter(Model.Ticket.Categorie_service.ilike(f"%{categorie}%"))
    
    # Filtrer par agent
    if agent_id:
        query = query.filter(Model.Ticket.Agent_id == agent_id)
    
    # Filtrer par période
    if date_debut:
        query = query.filter(Model.Ticket.Date_ >= date_debut)
    if date_fin:
        query = query.filter(Model.Ticket.Date_ <= date_fin)
    
    # Filtrer par statut (via le dernier événement)
    if statut:
        # Une Sous-requête pour obtenir le dernier statut de chaque ticket
        latest_events = db.query(
            Model.Event_ticket.Ticket_id,
            Model.Event_ticket.statut
        ).order_by(
            Model.Event_ticket.Ticket_id,
            desc(Model.Event_ticket.Date_event)
        ).distinct(Model.Event_ticket.Ticket_id).subquery()
        
        query = query.join(
            latest_events,
            Model.Ticket.Ticket_id == latest_events.c.Ticket_id
        ).filter(latest_events.c.statut == statut)
    
    return query.order_by(desc(Model.Ticket.Date_)).offset(skip).limit(limit).all()


def update_ticket(db: Session, ticket_id: int, ticket_update: schemas.TicketUpdate) -> Optional[Model.Ticket]:
    """Mettre à jour un ticket"""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    
    update_data = ticket_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ticket, field, value)
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int) -> bool:
    """Supprimer un ticket"""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return False
    
    db.delete(db_ticket)
    db.commit()
    return True


def get_ticket_current_status(db: Session, ticket_id: int) -> Optional[Model.StatutEnum]:
    """Récupérer le statut actuel d'un ticket"""
    latest_event = db.query(Model.Event_ticket).filter(
        Model.Event_ticket.Ticket_id == ticket_id
    ).order_by(desc(Model.Event_ticket.Date_event)).first()
    
    return latest_event.statut if latest_event else None


# CRUD EVENTS TICKETS

def create_ticket_event(
    db: Session, 
    agent_id: int, 
    ticket_id: int, 
    statut: Model.StatutEnum
) -> Model.Event_ticket:
    """Créer un nouvel événement pour un ticket"""
    # Vérifier que l'agent et le ticket existent
    if not get_agent(db, agent_id):
        raise ValueError(f"Agent avec ID {agent_id} n'existe pas")
    if not get_ticket(db, ticket_id):
        raise ValueError(f"Ticket avec ID {ticket_id} n'existe pas")
    
    db_event = Model.Event_ticket(
        Agent_id=agent_id,
        Ticket_id=ticket_id,
        Date_event=datetime.now(),
        statut=statut
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_ticket_events(db: Session, ticket_id: int) -> List[Model.Event_ticket]:
    """Récupérer tous les événements d'un ticket"""
    return db.query(Model.Event_ticket).filter(
        Model.Event_ticket.Ticket_id == ticket_id
    ).order_by(Model.Event_ticket.Date_event).all()


def update_ticket_status(
    db: Session, 
    ticket_id: int, 
    agent_id: int, 
    nouveau_statut: Model.StatutEnum
) -> Model.Event_ticket:
    """Mettre à jour le statut d'un ticket (créer un nouvel événement)"""
    # Vérifier que le ticket existe
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket avec ID {ticket_id} n'existe pas")
    
    # Vérifier que l'agent existe
    if not get_agent(db, agent_id):
        raise ValueError(f"Agent avec ID {agent_id} n'existe pas")
    
    # Récupérer le statut actuel
    statut_actuel = get_ticket_current_status(db, ticket_id)
    
    # Valider la transition de statut
    if not is_valid_status_transition(statut_actuel, nouveau_statut):
        raise ValueError(f"Transition invalide de {statut_actuel} vers {nouveau_statut}")
    
    return create_ticket_event(db, agent_id, ticket_id, nouveau_statut)


def is_valid_status_transition(statut_actuel: Optional[Model.StatutEnum], nouveau_statut: Model.StatutEnum) -> bool:
    """Valider si une transition de statut est autorisée"""
    # Règles de transition
    transitions_valides = {
        None: [Model.StatutEnum.en_attente],  # Création
        Model.StatutEnum.en_attente: [Model.StatutEnum.en_cours, Model.StatutEnum.annule],
        Model.StatutEnum.en_cours: [Model.StatutEnum.termine, Model.StatutEnum.annule, Model.StatutEnum.en_attente],
        Model.StatutEnum.termine: [Model.StatutEnum.en_cours],  # Réouverture possible
        Model.StatutEnum.annule: [Model.StatutEnum.en_attente]  # Réactivation possible
    }
    
    return nouveau_statut in transitions_valides.get(statut_actuel, [])


#STATISTIQUES GLOBALES

def get_global_statistics(db: Session) -> dict:
    """Récupérer les statistiques globales"""
    total_agents = db.query(Model.Agent).count()
    total_tickets = db.query(Model.Ticket).count()
    
    # Statistiques par statut
    stats_statut = {}
    for statut in Model.StatutEnum:
        # Compter les tickets avec ce statut comme dernier événement
        count = db.query(Model.Event_ticket).filter(
            Model.Event_ticket.statut == statut
        ).count()
        stats_statut[statut.value] = count
    
    # Statistiques par catégorie d'agent
    stats_categorie_agent = {}
    for categorie in Model.CategorieEnum:
        count = db.query(Model.Agent).filter(Model.Agent.Categorie == categorie).count()
        stats_categorie_agent[categorie.value] = count
    
    return {
        "total_agents": total_agents,
        "total_tickets": total_tickets,
        "tickets_par_statut": stats_statut,
        "agents_par_categorie": stats_categorie_agent,
        "date_generation": datetime.now().isoformat()
    }