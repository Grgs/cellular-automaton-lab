from __future__ import annotations

from backend.payload_types import CellTargetPayload, CellUpdatePayload, CellUpdatesPayload, TopologySpecRequestPayload

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


def blank_to_none(value: object) -> object | None:
    if value in (None, ""):
        return None
    return value


class OptionalIntValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: int | None = None

    @field_validator("value", mode="before")
    @classmethod
    def normalize_blank(cls, value: object) -> object | None:
        return blank_to_none(value)


class OptionalFloatValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: float | None = None

    @field_validator("value", mode="before")
    @classmethod
    def normalize_blank(cls, value: object) -> object | None:
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
    def normalize_blank(cls, value: object) -> object | None:
        return blank_to_none(value)


class IdCellTargetModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: StrictStr

    def to_payload(self) -> CellTargetPayload:
        return {"id": self.id}


class IdCellUpdateModel(IdCellTargetModel):
    state: int

    def to_payload(self) -> CellUpdatePayload:
        return {"id": self.id, "state": self.state}


class CellUpdatesPayloadModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cells: list[IdCellUpdateModel] = Field(min_length=1)


class TopologySpecValueModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tiling_family: StrictStr | None = None
    adjacency_mode: StrictStr | None = None
    sizing_mode: StrictStr | None = None
    width: int | None = None
    height: int | None = None
    patch_depth: int | None = None
    unsafe_size_override: bool | None = None

    @field_validator("tiling_family", "adjacency_mode", "sizing_mode", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: object) -> object | None:
        return blank_to_none(value)

    @field_validator("width", "height", "patch_depth", mode="before")
    @classmethod
    def normalize_optional_ints(cls, value: object) -> object | None:
        return blank_to_none(value)

    @field_validator("unsafe_size_override", mode="before")
    @classmethod
    def normalize_optional_bool(cls, value: object) -> object | None:
        return blank_to_none(value)

    def to_payload(self) -> TopologySpecRequestPayload:
        payload: TopologySpecRequestPayload = {
            "tiling_family": self.tiling_family or "",
            "adjacency_mode": self.adjacency_mode or "",
            "sizing_mode": self.sizing_mode or "",
            "width": self.width,
            "height": self.height,
            "patch_depth": self.patch_depth,
        }
        if self.unsafe_size_override is not None:
            payload["unsafe_size_override"] = bool(self.unsafe_size_override)
        return payload


class ConfigUpdateRequestModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    speed: float | None = None
    rule: StrictStr | None = None
    topology_spec: TopologySpecValueModel | None = None

    @field_validator("rule", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: object) -> object | None:
        return blank_to_none(value)

    @field_validator("speed", mode="before")
    @classmethod
    def normalize_optional_float(cls, value: object) -> object | None:
        return blank_to_none(value)

class ResetRequestModel(ConfigUpdateRequestModel):
    randomize: bool = False
