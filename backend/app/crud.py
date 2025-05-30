import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    print(f"Authenticating user: {email}, found: {db_user is not None}")
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def get_worker_stats_by_id(*, worker_id: str) -> dict | None:
    """
    Retrieves Celery worker statistics for a specific worker.
    Returns comprehensive worker stats including uptime, memory usage, and task counts.
    """
    from app.celery_app import celery_app

    try:
        # Get inspection interface
        i = celery_app.control.inspect()

        # Get worker statistics
        stats_data = i.stats() or {}

        # Look for the specific worker
        for worker_name, worker_info in stats_data.items():
            if worker_name == worker_id or worker_name.endswith(f"@{worker_id}"):
                # Extract key statistics from worker info and return in the new format
                return {
                    "worker_id": worker_id,
                    "worker_name": worker_name,
                    "status": "ONLINE",  # Worker is online if we can get stats
                    "uptime": worker_info.get("uptime", 0),
                    "pid": worker_info.get("pid"),
                    "clock": worker_info.get("clock", 0),
                    "prefetch_count": worker_info.get("prefetch_count", 0),
                    "pool": worker_info.get("pool", {}),
                    "broker": worker_info.get("broker", {}),
                    "total_tasks": worker_info.get("total", {}),
                    "rusage": worker_info.get("rusage", {}),
                }

        # If not found in stats, try to ping the specific worker
        ping_data = i.ping() or {}
        for worker_name, ping_response in ping_data.items():
            if (
                worker_name == worker_id or worker_name.endswith(f"@{worker_id}")
            ) and ping_response.get("ok") == "pong":
                return {
                    "worker_id": worker_id,
                    "worker_name": worker_name,
                    "status": "ONLINE",
                    "uptime": None,
                    "pid": None,
                    "clock": None,
                    "prefetch_count": None,
                    "pool": None,
                    "broker": None,
                    "total_tasks": None,
                    "rusage": None,
                }

        # Worker not found
        return None

    except Exception as e:
        print(f"Error retrieving worker stats from Celery for {worker_id}: {e}")
        # Return None if there's an error
        return None
