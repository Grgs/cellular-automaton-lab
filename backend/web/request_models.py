from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


def blank_to_none(value: Any) -> Any:
    if value in (None, ""):
        return None
    return value


class OptionalIntValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: int | None = None

    @field_validator("value", mode="before")
    @classmethod
    def normalize_blank(cls, value: Any) -> Any:
        return blank_to_none(value)


class OptionalFloatValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: float | None = None

    @field_validator("value", mode="before")
    @classmethod
    def normalize_blank(cls, value: Any) -> Any:
        return blank_to_none(value)


class RequiredIntValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: int


class StateValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: int


class CellIdValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: StrictStr


class RuleNameValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: StrictStr | None = None

    @field_validator("value", mode="before")
    @classmethod
    def normalize_blank(cls, value: Any) -> Any:
        return blank_to_none(value)


class IdCellTargetModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: StrictStr


class IdCellUpdateModel(IdCellTargetModel):
    state: int


class CellUpdatesPayloadModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cells: list[dict[str, Any]] = Field(min_length=1)


class TopologySpecValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tiling_family: StrictStr | None = None
    adjacency_mode: StrictStr | None = None
    sizing_mode: StrictStr | None = None
    width: int | None = None
    height: int | None = None
    patch_depth: int | None = None

    @field_validator("tiling_family", "adjacency_mode", "sizing_mode", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: Any) -> Any:
        return blank_to_none(value)

    @field_validator("width", "height", "patch_depth", mode="before")
    @classmethod
    def normalize_optional_ints(cls, value: Any) -> Any:
        return blank_to_none(value)


class ConfigUpdateRequestModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    speed: float | None = None
    rule: StrictStr | None = None
    topology_spec: TopologySpecValueModel | None = None

    @field_validator("rule", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: Any) -> Any:
        return blank_to_none(value)

    @field_validator("speed", mode="before")
    @classmethod
    def normalize_optional_float(cls, value: Any) -> Any:
        return blank_to_none(value)

class ResetRequestModel(ConfigUpdateRequestModel):
    randomize: bool = False
