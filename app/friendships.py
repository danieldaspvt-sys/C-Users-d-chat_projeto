from sqlalchemy import and_, func, or_
from .models import Friendship, User, db


def _find_user_by_username(username):
    normalized = (username or "").strip().replace("@", "").lower()
    if not normalized:
        return None
    return User.query.filter(func.lower(User.username) == normalized).first()


def are_friends(user_a_id, user_b_id):
    rel = Friendship.query.filter(
        Friendship.status == "accepted",
        or_(
            and_(Friendship.requester_id == user_a_id, Friendship.addressee_id == user_b_id),
            and_(Friendship.requester_id == user_b_id, Friendship.addressee_id == user_a_id),
        ),
    ).first()
    return rel is not None


def get_friends(user_id):
    accepted = Friendship.query.filter(
        Friendship.status == "accepted",
        or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id),
    ).all()

    friend_ids = [
        item.addressee_id if item.requester_id == user_id else item.requester_id
        for item in accepted
    ]

    if not friend_ids:
        return []

    return User.query.filter(User.id.in_(friend_ids)).order_by(User.username.asc()).all()


def pending_requests(user_id):
    requests = Friendship.query.filter_by(addressee_id=user_id, status="pending").all()
    requester_ids = [item.requester_id for item in requests]
    if not requester_ids:
        return []
    return User.query.filter(User.id.in_(requester_ids)).order_by(User.username.asc()).all()


def outgoing_requests(user_id):
    requests = Friendship.query.filter_by(requester_id=user_id, status="pending").all()
    addressee_ids = [item.addressee_id for item in requests]
    if not addressee_ids:
        return []
    return User.query.filter(User.id.in_(addressee_ids)).order_by(User.username.asc()).all()


def send_request(requester_id, addressee_username):
    addressee = _find_user_by_username(addressee_username)
    if not addressee or addressee.id == requester_id:
        return False, "Usuário inválido"

    existing = Friendship.query.filter(
        or_(
            and_(Friendship.requester_id == requester_id, Friendship.addressee_id == addressee.id),
            and_(Friendship.requester_id == addressee.id, Friendship.addressee_id == requester_id),
        )
    ).first()

    if existing:
        if existing.status == "accepted":
            return False, "Vocês já são amigos"

        if existing.status == "pending":
            if existing.requester_id == addressee.id and existing.addressee_id == requester_id:
                existing.status = "accepted"
                db.session.commit()
                return True, "Amizade confirmada automaticamente!"
            return False, "Solicitação já pendente"

        existing.status = "pending"
        existing.requester_id = requester_id
        existing.addressee_id = addressee.id
        db.session.commit()
        return True, "Solicitação reenviada"

    db.session.add(Friendship(requester_id=requester_id, addressee_id=addressee.id))
    db.session.commit()
    return True, "Solicitação enviada"


def respond_request(addressee_id, requester_id, action):
    relation = Friendship.query.filter_by(
        requester_id=requester_id,
        addressee_id=addressee_id,
        status="pending",
    ).first()

    if not relation:
        return False, "Solicitação não encontrada"

    if action == "accept":
        relation.status = "accepted"
        db.session.commit()
        return True, "Solicitação aceita"

    if action == "reject":
        relation.status = "rejected"
        db.session.commit()
        return True, "Solicitação recusada"

    return False, "Ação inválida"
