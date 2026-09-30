from decimal import Decimal

from pydantic import ValidationError

from schemas import RecommendationResponse
from services import gemini_service, mock_catalog


def _validated_ai_result(candidate: dict | None, budget: Decimal, fallback: dict) -> dict | None:
    if not candidate:
        return None
    try:
        merged = {**fallback, **candidate}
        merged.setdefault("allocations", fallback.get("allocations", []))
        result = RecommendationResponse.model_validate(merged)
        recommendations_total = sum((row.estimated_total for row in result.recommendations), Decimal(0))
        if (recommendations_total > budget
            or result.total_estimated != recommendations_total
            or result.remaining_budget != budget - recommendations_total
            or any(row.estimated_total != row.estimated_price * row.quantity for row in result.recommendations)):
            return None
        normalized = result.model_dump(mode="json")
        normalized["total_estimated"] = str(recommendations_total)
        normalized["remaining_budget"] = str(budget - recommendations_total)
        return normalized
    except (ValidationError, TypeError, ValueError):
        return None


def generate_home_recommendations(payload: dict) -> tuple[dict, bool]:
    fallback = mock_catalog.home_recommendations(payload)
    result = _validated_ai_result(gemini_service.generate_home_recommendations(payload, fallback), Decimal(payload["total_budget"]), fallback)
    return (result, True) if result else (fallback, False)


def generate_party_recommendations(payload: dict) -> tuple[dict, bool]:
    fallback = mock_catalog.party_recommendations(payload)
    result = _validated_ai_result(gemini_service.generate_party_recommendations(payload, fallback), Decimal(payload["total_budget"]), fallback)
    return (result, True) if result else (fallback, False)


def generate_jewelry_recommendations(payload: dict, outfit_analysis: str = "", image: tuple[bytes, str] | None = None) -> tuple[dict, bool]:
    fallback = mock_catalog.jewelry_recommendations(payload, outfit_analysis)
    result = _validated_ai_result(gemini_service.generate_jewelry_recommendations(payload, fallback, outfit_analysis, image), Decimal(payload["budget"]), fallback)
    return (result, True) if result else (fallback, False)