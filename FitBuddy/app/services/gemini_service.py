import json
from functools import lru_cache

from pydantic import ValidationError

from ..config import settings
from ..schemas import DayPlan, NutritionOutput, UserInput, WorkoutPlanOutput


class GeminiServiceError(RuntimeError):
    """Raised when Gemini cannot produce a usable response."""


@lru_cache
def _client():
    from google import genai

    if not settings.gemini_api_key:
        raise GeminiServiceError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=settings.gemini_api_key)


def _extract_json(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    json.loads(value)
    return value


def _generate_structured(model: str, prompt: str, schema: type) -> str:
    try:
        from google.genai import types

        response = _client().models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=5000,
            ),
        )
        if not response.text:
            raise GeminiServiceError("Gemini returned an empty response.")
        raw = _extract_json(response.text)
        validated = schema.model_validate_json(raw)
        return validated.model_dump_json(indent=2)
    except GeminiServiceError:
        raise
    except (json.JSONDecodeError, ValidationError) as exc:
        raise GeminiServiceError(f"Gemini returned invalid structured data: {exc}") from exc
    except Exception as exc:
        raise GeminiServiceError(f"Gemini request failed: {exc}") from exc


def _fallback_or_raise(error: GeminiServiceError, fallback: str) -> str:
    if settings.ai_fallback_to_demo:
        return fallback
    raise error


def generate_workout_gemini(data: UserInput) -> str:
    if settings.demo_mode or not settings.gemini_api_key:
        return demo_workout(data)
    prompt = f"""
You are FitBuddy, a conservative fitness-planning assistant. Create a safe, practical 7-day
workout plan for this user profile:
- Name: {data.name}
- Age: {data.age}
- Weight: {data.weight} kg
- Goal: {data.goal}
- Intensity: {data.intensity}

Return exactly 7 day entries. Each day needs a clear focus, a 5-10 minute warm-up,
3-6 exercises with sets/reps OR duration, and a cooldown/recovery instruction.
Include at least one recovery/rest-oriented day. Avoid diagnosing conditions, medication,
extreme calorie restriction, or unsafe claims. Use accessible exercises and give alternatives
where appropriate. Keep the plan useful without assuming gym equipment.
Safety note should say users with pain, injury, chronic conditions, or medical concerns should
seek professional advice before exercising.
"""
    try:
        return _generate_structured(settings.workout_model, prompt, WorkoutPlanOutput)
    except GeminiServiceError as exc:
        return _fallback_or_raise(exc, demo_workout(data))


def generate_nutrition_tip_with_flash(data: UserInput) -> str:
    if settings.demo_mode or not settings.gemini_api_key:
        return demo_nutrition(data)
    prompt = f"""
Create one concise nutrition/recovery suggestion for a FitBuddy user.
Goal: {data.goal}
Intensity: {data.intensity}
Weight: {data.weight} kg
Age: {data.age}

Avoid personalized medical nutrition advice and avoid prescribing supplements or exact
calorie targets. Prefer practical habits such as balanced meals, protein-rich foods,
hydration, sleep, and recovery. Return a short tip and one concrete action.
"""
    try:
        return _generate_structured(settings.fast_model, prompt, NutritionOutput)
    except GeminiServiceError as exc:
        return _fallback_or_raise(exc, demo_nutrition(data))


def update_workout_plan(original_plan: str, data: UserInput, feedback: str) -> str:
    if settings.demo_mode or not settings.gemini_api_key:
        return demo_update(original_plan, feedback)
    prompt = f"""
You are revising a FitBuddy 7-day workout plan.
User profile: age {data.age}, weight {data.weight} kg, goal {data.goal}, intensity {data.intensity}.
Original plan:
{original_plan}

User feedback:
{feedback}

Return a complete replacement 7-day plan, not just a list of changes. Respect the requested
feedback where it is safe. Keep at least one recovery/rest-oriented day, avoid dangerous
exercise prescriptions, and include a safety note. Use the same structured schema.
"""
    try:
        return _generate_structured(settings.workout_model, prompt, WorkoutPlanOutput)
    except GeminiServiceError as exc:
        return _fallback_or_raise(exc, demo_update(original_plan, feedback))


def demo_workout(data: UserInput) -> str:
    return WorkoutPlanOutput(
        title=f"7-Day {data.goal.title()} Plan",
        safety_note="Start gradually. Stop if you experience pain, dizziness, or unusual symptoms; seek professional advice for injuries or medical concerns.",
        days=[
            DayPlan(day="Day 1", focus="Full Body", warm_up="5-10 min brisk walk + mobility", exercises=["Bodyweight squat — 3 x 10", "Incline push-up — 3 x 8", "Glute bridge — 3 x 12", "Plank — 3 x 20 sec"], cooldown="5 min easy walking and stretching"),
            DayPlan(day="Day 2", focus="Cardio", warm_up="5 min easy walk", exercises=["Brisk walk — 25 min", "Step-ups — 3 x 10/side", "Marching high knees — 3 x 30 sec"], cooldown="5 min slow walk + calf stretch"),
            DayPlan(day="Day 3", focus="Lower Body", warm_up="5-10 min mobility", exercises=["Squat — 3 x 10", "Reverse lunge — 3 x 8/side", "Glute bridge — 3 x 12", "Calf raise — 3 x 15"], cooldown="Lower-body stretches for 5 min"),
            DayPlan(day="Day 4", focus="Recovery & Mobility", warm_up="5 min gentle walking", exercises=["Easy walk — 15-20 min", "Cat-cow — 2 x 8", "Hip mobility — 5 min", "Gentle stretching — 8 min"], cooldown="Relaxed breathing for 3-5 min"),
            DayPlan(day="Day 5", focus="Upper Body + Core", warm_up="5-10 min shoulder and arm mobility", exercises=["Incline push-up — 3 x 8", "Backpack row — 3 x 10", "Dead bug — 3 x 8/side", "Side plank — 2 x 20 sec/side"], cooldown="Upper-body stretching for 5 min"),
            DayPlan(day="Day 6", focus="Goal-Focused Cardio", warm_up="5 min easy walk", exercises=["Brisk walk or cycling — 25-30 min", "Step-ups — 3 x 10/side", "Easy intervals — 5 x 30 sec"], cooldown="5 min easy pace + stretching"),
            DayPlan(day="Day 7", focus="Rest", warm_up="Optional gentle mobility", exercises=["Rest day", "Optional relaxed walk — 15-20 min"], cooldown="Prioritize hydration, sleep, and recovery"),
        ],
    ).model_dump_json(indent=2)


def demo_nutrition(data: UserInput) -> str:
    return NutritionOutput(
        tip="Build balanced meals around protein-rich foods, vegetables or fruit, whole grains or other carbohydrate sources, and adequate fluids.",
        action="Include a protein-rich food in your next main meal and drink water regularly.",
    ).model_dump_json(indent=2)


def demo_update(original_plan: str, feedback: str) -> str:
    try:
        plan = WorkoutPlanOutput.model_validate_json(original_plan)
        plan.title = f"{plan.title} — Updated"
        plan.safety_note += " Follow the adjusted plan gradually and stop if symptoms occur."
        plan.days[0].focus = f"{plan.days[0].focus} (feedback: {feedback.strip()[:120]})"
        return plan.model_dump_json(indent=2)
    except ValidationError:
        return original_plan
