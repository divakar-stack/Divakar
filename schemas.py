from decimal import Decimal
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=2, max_length=40)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.lower()
        if "@" not in value or value.startswith("@") or value.endswith("@") or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        return value


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()


class HomeItem(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=0, le=100)


class HomePlannerInput(BaseModel):
    total_budget: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    home_type: str = Field(min_length=2, max_length=80)
    room_count: int = Field(gt=0, le=100)
    room_details: str = Field(min_length=2, max_length=1000)
    style_preference: str = Field(min_length=2, max_length=80)
    items: list[HomeItem] = Field(min_length=1, max_length=30)


class PartyPlannerInput(BaseModel):
    total_budget: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    guest_count: int = Field(gt=0, le=10000)
    event_type: str = Field(min_length=2, max_length=80)
    venue_preference: str = Field(min_length=2, max_length=200)
    event_date: date
    food_preference: str = Field(min_length=2, max_length=200)
    decoration_preference: str = Field(min_length=2, max_length=200)
    entertainment_preference: str = Field(min_length=2, max_length=200)
    accommodation_required: bool = False


class JewelryPlannerInput(BaseModel):
    budget: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    occasion: str = Field(min_length=2, max_length=80)
    jewelry_type: str = Field(min_length=2, max_length=80)
    style_preference: str = Field(min_length=2, max_length=80)
    preferred_material: str = Field(min_length=2, max_length=80)
    color_preference: str = Field(min_length=2, max_length=80)
    outfit_description: str = Field(min_length=2, max_length=1000)


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    category: str = ""
    estimated_price: Decimal = Field(ge=0)
    quantity: int = Field(default=1, ge=0)
    estimated_total: Decimal = Field(ge=0)
    platform: str = "Local catalog"
    reason: str = ""
    style: str = ""
    budget_status: Literal["within", "over"] = "within"
    product_url: str | None = None


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: str
    recommendations: list[Recommendation]
    total_estimated: Decimal = Field(ge=0)
    remaining_budget: Decimal