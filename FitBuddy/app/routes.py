import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .crud import delete_user, get_all_users, get_user, save_plan, save_user, update_plan
from .database import get_db
from .config import BASE_DIR
from .schemas import FeedbackRequest, UserInput
from .services.gemini_service import (
    GeminiServiceError,
    generate_nutrition_tip_with_flash,
    generate_workout_gemini,
    update_workout_plan,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _json_or_text(value: str) -> str:
    try:
        obj = json.loads(value)
        return json.dumps(obj, indent=2)
    except json.JSONDecodeError:
        return value


def _result_context(request: Request, user, plan, message: str | None = None):
    return {
        "request": request,
        "user": user,
        "plan": plan,
        "workout_plan": _json_or_text(plan.updated_plan or plan.original_plan),
        "original_plan": _json_or_text(plan.original_plan),
        "nutrition_tip": _json_or_text(plan.nutrition_tip),
        "message": message,
    }


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    user_id: Annotated[str, Form()],
    name: Annotated[str, Form()],
    age: Annotated[int, Form()],
    weight: Annotated[float, Form()],
    goal: Annotated[str, Form()],
    intensity: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    try:
        data = UserInput(user_id=user_id, name=name, age=age, weight=weight, goal=goal, intensity=intensity)
        workout = generate_workout_gemini(data)
        nutrition = generate_nutrition_tip_with_flash(data)
        user = save_user(db, data)
        plan = save_plan(db, user, workout, nutrition)
        return templates.TemplateResponse(request, "result.html", _result_context(request, user, plan))
    except (ValueError, GeminiServiceError) as exc:
        return templates.TemplateResponse(request, "error.html", {"error": str(exc)}, status_code=400)


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: Annotated[str, Form()],
    feedback: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    try:
        data_request = FeedbackRequest(user_id=user_id, feedback=feedback)
        user = get_user(db, data_request.user_id)
        if not user or not user.plan:
            raise ValueError("User or workout plan not found.")
        data = UserInput(user_id=user.user_id, name=user.name, age=user.age, weight=user.weight, goal=user.goal, intensity=user.intensity)
        updated = update_workout_plan(user.plan.original_plan, data, data_request.feedback)
        nutrition = generate_nutrition_tip_with_flash(data)
        plan = update_plan(db, user, updated, nutrition, data_request.feedback)
        return templates.TemplateResponse(request, "result.html", _result_context(request, user, plan, "Your plan was updated from the feedback."))
    except (ValueError, GeminiServiceError) as exc:
        return templates.TemplateResponse(request, "error.html", {"error": str(exc)}, status_code=400)


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, db: Session = Depends(get_db)):
    users = get_all_users(db)
    return templates.TemplateResponse(request, "all_users.html", {"users": users})


@router.post("/delete-user/{user_id}")
def remove_user(user_id: str, db: Session = Depends(get_db)):
    if not delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse("/view-all-users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/api/health")
def health():
    return {"status": "ok", "service": "FitBuddy"}


@router.post("/api/generate-workout")
def api_generate_workout(data: UserInput, db: Session = Depends(get_db)):
    try:
        workout = generate_workout_gemini(data)
        nutrition = generate_nutrition_tip_with_flash(data)
        user = save_user(db, data)
        plan = save_plan(db, user, workout, nutrition)
        return {"user_id": user.user_id, "workout_plan": json.loads(workout), "nutrition": json.loads(nutrition)}
    except GeminiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/submit-feedback")
def api_submit_feedback(data: FeedbackRequest, db: Session = Depends(get_db)):
    user = get_user(db, data.user_id)
    if not user or not user.plan:
        raise HTTPException(status_code=404, detail="User or workout plan not found")
    profile = UserInput(user_id=user.user_id, name=user.name, age=user.age, weight=user.weight, goal=user.goal, intensity=user.intensity)
    try:
        updated = update_workout_plan(user.plan.original_plan, profile, data.feedback)
        nutrition = generate_nutrition_tip_with_flash(profile)
        plan = update_plan(db, user, updated, nutrition, data.feedback)
        return {"user_id": user.user_id, "updated_plan": json.loads(plan.updated_plan or "{}"), "nutrition": json.loads(plan.nutrition_tip)}
    except GeminiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/api/users")
def api_users(db: Session = Depends(get_db)):
    return [
        {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "created_at": user.created_at.isoformat(),
            "has_updated_plan": bool(user.plan and user.plan.updated_plan),
        }
        for user in get_all_users(db)
    ]
