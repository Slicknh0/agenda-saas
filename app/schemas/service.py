from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    duration_minutes: int = Field(gt=0, le=24 * 60)
    price_cents: int = Field(ge=0)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    duration_minutes: int | None = Field(default=None, gt=0, le=24 * 60)
    price_cents: int | None = Field(default=None, ge=0)
    active: bool | None = None


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_minutes: int
    price_cents: int
    active: bool
