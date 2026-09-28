from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .models import User, WorkoutPlan
from .schemas import UserInput


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id).options(joinedload(User.plan)))


def save_user(db: Session, data: UserInput) -> User:
    user = get_user(db, data.user_id)
    if user:
        user.name = data.name
        user.age = data.age
        user.weight = data.weight
        user.goal = data.goal
        user.intensity = data.intensity
    else:
        user = User(**data.model_dump())
        db.add(user)
    db.flush()
    return user


def save_plan(db: Session, user: User, original_plan: str, nutrition_tip: str) -> WorkoutPlan:
    if user.plan:
        user.plan.original_plan = original_plan
        user.plan.updated_plan = None
        user.plan.feedback = None
        user.plan.nutrition_tip = nutrition_tip
        user.plan.updated_at = None
        plan = user.plan
    else:
        plan = WorkoutPlan(user_pk=user.id, original_plan=original_plan, nutrition_tip=nutrition_tip)
        db.add(plan)
    db.commit()
    db.refresh(user)
    return plan


def update_plan(db: Session, user: User, updated_plan: str, nutrition_tip: str, feedback: str) -> WorkoutPlan:
    if not user.plan:
        raise ValueError("No workout plan exists for this user.")
    user.plan.updated_plan = updated_plan
    user.plan.nutrition_tip = nutrition_tip
    user.plan.feedback = feedback
    user.plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user.plan)
    return user.plan


def get_all_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).options(joinedload(User.plan)).order_by(User.created_at.desc())).unique())


def delete_user(db: Session, user_id: str) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
