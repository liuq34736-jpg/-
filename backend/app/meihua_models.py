"""Day 4 HTTP whitelist. Questions are context, never calculation inputs."""

from datetime import datetime, timedelta, timezone
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CHINA = timezone(timedelta(hours=8), name="Asia/Shanghai")
API_VERSION = "meihua_service_adapter_v1"


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


def china_moment(value: str) -> datetime:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})", value):
        raise ValueError("invalid_timestamp")
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.utcoffset() is None or abs(moment.utcoffset()) > timedelta(hours=14):
        raise ValueError("invalid_offset")
    moment = moment.astimezone(CHINA)
    if not 2000 <= moment.year <= 2099:
        raise ValueError("outside_supported_range")
    return moment


class BaseInput(PublicModel):
    question_text: Annotated[str, Field(max_length=500)] = ""
    cast_at: Annotated[str, Field(min_length=17, max_length=35)] = Field(
        default_factory=lambda: datetime.now(CHINA).isoformat(timespec="seconds"))

    @field_validator("cast_at")
    @classmethod
    def valid_moment(cls, value):
        china_moment(value)
        return value

    @field_validator("question_text")
    @classmethod
    def valid_question(cls, value):
        if any(ord(c) < 32 and c not in "\n\r\t" for c in value) or any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ValueError("invalid_question")
        return value.strip()


class ManualInput(BaseInput):
    input_mode: Literal["manual_hexagram"]
    hexagram_id: Annotated[int, Field(ge=1, le=64)]
    moving_line: Annotated[int, Field(ge=1, le=6)]


class TimeInput(BaseInput):
    input_mode: Literal["time_cast"]


CastingInput = Annotated[ManualInput | TimeInput, Field(discriminator="input_mode")]
Line = Annotated[int, Field(strict=True, ge=0, le=1)]
Trigram = Literal["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
Element = Literal["木", "火", "土", "金", "水"]
Role = Literal["original_hexagram", "moving_line", "mutual_hexagram", "changed_hexagram"]


class HexagramView(PublicModel):
    id: Annotated[int, Field(ge=1, le=64)]
    name: str
    full_name: str
    lines: Annotated[list[Line], Field(min_length=6, max_length=6)]
    binary: Annotated[str, Field(pattern=r"^[01]{6}$")]
    upper_trigram: Trigram
    lower_trigram: Trigram


class CatalogEntry(HexagramView):
    line_names: Annotated[list[str], Field(min_length=6, max_length=6)]


class CatalogResult(PublicModel):
    api_version: Literal["meihua_service_adapter_v1"]
    timezone: Literal["Asia/Shanghai"]
    entries: Annotated[list[CatalogEntry], Field(min_length=64, max_length=64)]


class MovingLineView(PublicModel):
    position: Annotated[int, Field(ge=1, le=6)]
    name: str
    polarity: Line


class BodyUseView(PublicModel):
    rule_version: Literal["moving_trigram_is_yong_v1"]
    body_trigram: Trigram
    yong_trigram: Trigram
    body_element: Element
    yong_element: Element
    relation: Literal["body_generates_yong", "yong_generates_body", "body_controls_yong", "yong_controls_body", "same_element"]
    relation_text: str


class TrigramStrength(PublicModel):
    trigram: Trigram
    element: Element
    state: Literal["wang", "shuai", "neutral"]
    state_label: Literal["旺", "衰", "平"]


class AuxiliaryStrength(PublicModel):
    upper: TrigramStrength
    lower: TrigramStrength


class StrengthView(PublicModel):
    rule_version: Literal["meihua_strength_v1"]
    timezone: Literal["Asia/Shanghai"]
    solar_term_month_branch: str
    ruling_element: Element
    active_solar_term: str
    active_solar_term_time: str
    next_solar_term: str
    next_solar_term_time: str
    strength_boundary_time: str
    next_month_boundary_time: str
    body: TrigramStrength
    yong: TrigramStrength
    mutual: AuxiliaryStrength
    changed: AuxiliaryStrength
    auxiliary_weight: Literal["auxiliary_strength"]
    solar_term_source: str


class TimeCalculation(PublicModel):
    lunar_year: int
    lunar_month: int
    lunar_day: int
    is_leap_month: bool
    lunar_datetime: str
    year_branch: str
    year_branch_number: int
    hour_branch: str
    hour_branch_number: int
    upper_total: int
    upper_remainder: int
    lower_total: int
    lower_remainder: int
    moving_total: int
    moving_remainder: int
    day_boundary_mode: Literal["midnight"]


class Versions(PublicModel):
    production_version: Literal["1.2.0"]
    casting_version: Literal["manual_hexagram_v1", "traditional_meihua_datetime_v1"]
    analysis_version: Literal["meihua_analysis_v1"]
    interpretation_version: Literal["meihua_interpretation_v1"]
    body_use_version: Literal["moving_trigram_is_yong_v1"]
    strength_version: Literal["meihua_strength_v1"]
    source_corpus_version: Literal["canonical_meihua_corpus_v1"]
    semantic_frame_version: Literal["verified_semantic_frame_v1"]


class FactEvidence(PublicModel):
    type: str
    rule_version: str


class StandardUnit(PublicModel):
    type: str
    statement: Annotated[str, Field(max_length=2000)]
    evidence: Annotated[list[FactEvidence], Field(min_length=1)]


class SourceReference(PublicModel):
    evidence_id: str
    role: Role
    section_type: str
    text: Annotated[str, Field(max_length=15000)]
    source_title: str
    edition: str
    url: Annotated[str, Field(pattern=r"^https://")]
    volume: str
    location: str
    original_pages: None = None
    verification_status: Literal["machine_verified", "verified"]
    variant_present: bool


class StandardMeaning(PublicModel):
    role: Role
    text: Annotated[str, Field(max_length=4000)]
    status: Literal["SEMANTIC_APPROVED", "structure_fallback"]
    source_evidence_ids: list[str]


class CalculationResult(PublicModel):
    api_version: Literal["meihua_service_adapter_v1"]
    input_mode: Literal["manual_hexagram", "time_cast"]
    cast_at: str
    timezone: Literal["Asia/Shanghai"]
    line_order: Literal["bottom_up"]
    original_hexagram: HexagramView
    moving_line: MovingLineView
    mutual_hexagram: HexagramView
    changed_hexagram: HexagramView
    body_use: BodyUseView
    strength: StrengthView
    time_calculation: TimeCalculation | None
    versions: Versions
    interpretation_units: list[StandardUnit]
    standard_meanings: Annotated[list[StandardMeaning], Field(min_length=4, max_length=4)]
    source_references: list[SourceReference]
    ai_used: Literal[False]
    history_saved: Literal[False]


class ReadingResponse(CalculationResult):
    question_text: str
    question_applied_to_calculation: Literal[False]
