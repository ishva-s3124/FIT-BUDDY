from typing import Literal

from pydantic import BaseModel, Field, field_validator

Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility", "endurance"]
Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    user_id: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=25, le=350)
    goal: Goal
    intensity: Intensity

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.strip().split())


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=50)
    feedback: str = Field(min_length=3, max_length=2000)


class DayPlan(BaseModel):
    day: str
    focus: str
    warm_up: str
    exercises: list[str]
    cooldown: str


class WorkoutPlanOutput(BaseModel):
    title: str
    safety_note: str
    days: list[DayPlan] = Field(min_length=7, max_length=7)


class NutritionOutput(BaseModel):
    tip: str
    action: str
