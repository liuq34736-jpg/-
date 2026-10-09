"""Browser response whitelist, distinct from internal review/receipt structures."""

from typing import Literal
from pydantic import Field, model_validator
from backend.app.meihua_models import PublicModel, ReadingResponse, SourceReference, Trigram, Element


class QuoteView(PublicModel):
    evidence_id: str
    quote: str


class ConditionView(PublicModel):
    id: str
    kind: str
    text: str
    source_evidence_ids: list[str] = Field(min_length=1)
    source_quotes: list[QuoteView] = Field(min_length=1)
    satisfaction: Literal["unknown"] = "unknown"


class BranchView(ConditionView):
    direction: Literal["favorable", "adverse", "undetermined"]
    condition_ids: list[str]


class FactorView(PublicModel):
    id: str
    text: str
    layer: Literal["primary", "qualifier", "reviewed_line", "auxiliary"]
    scope: str
    rule_ids: list[str]
    condition_ids: list[str]
    source_evidence_ids: list[str]


class AuxiliaryItemView(PublicModel):
    side: Literal["lower", "upper"]
    trigram: Trigram
    element: Element
    state_label: Literal["旺", "衰", "平"]
    relation_to_original_body: str
    status: Literal["reference_only", "context_only", "auxiliary_factor"]


class AuxiliaryView(PublicModel):
    role: Literal["mutual_hexagram", "changed_hexagram"]
    name: str
    items: list[AuxiliaryItemView]
    note: str


class NoticeView(PublicModel):
    type: str
    text: str
    rule_id: str


class RuleView(PublicModel):
    rule_id: str
    basis: str
    summary: str
    source_ids: list[str]


class RuleSourceView(PublicModel):
    source_id: str
    title: str
    edition: str
    volume: str
    location: str
    pdf_pages: list[int]
    printed_pages: list[str]
    url: str = Field(pattern=r"^https://")
    excerpt: str
    limits: str
    review_method: str


class ReviewProvenanceView(PublicModel):
    rule_version: str
    review_scope: Literal["offline_individual_condition_review"]
    human_verified: Literal[False]
    is_production_signature: Literal[False]


class JudgementView(PublicModel):
    preview_version: Literal["traditional_judgement_web_preview_v1"]
    policy_version: Literal["traditional_condition_synthesis_v1"]
    registry_version: Literal["day6ab_readonly_registry_v1"]
    review_status: Literal["bounded", "branch_unresolved", "unreviewed", "not_eligible", "evidence_unavailable"]
    eligible_for_condition_review: bool
    finite_synthesis_available: bool
    direction: Literal["favorable", "adverse", "mixed"] | None
    label: str
    summary: str
    scope: Literal["bounded_reviewed_synthesis", "conditional_branches_only", "structure_only"]
    body_use_baseline: Literal["favorable", "adverse"] | None
    conditions: list[ConditionView]
    branches: list[BranchView]
    branch_relationship: Literal["alternative_not_simultaneous", "joint_source_constraints"] | None
    scope_limits: list[ConditionView]
    favorable_factors: list[FactorView]
    adverse_factors: list[FactorView]
    strength_modifiers: list[FactorView]
    auxiliary_analysis: list[AuxiliaryView]
    conflicts: list[NoticeView]
    auxiliary_divergences: list[NoticeView]
    uncertainties: list[NoticeView]
    rules: list[RuleView]
    rule_sources: list[RuleSourceView]
    classical_sources: list[SourceReference]
    review_provenance: ReviewProvenanceView | None
    real_world_conditions: Literal["unknown"]
    question_used_to_satisfy_conditions: Literal[False]
    is_final_event_outcome: Literal[False]
    ai_used: Literal[False]
    history_written: Literal[False]

    @model_validator(mode="after")
    def enforce_scope(self):
        reviewed = self.review_status in {"bounded", "branch_unresolved"}
        if self.eligible_for_condition_review != reviewed or self.finite_synthesis_available != (self.review_status == "bounded"):
            raise ValueError("invalid_preview_eligibility")
        if (self.direction is not None) != (self.review_status == "bounded"):
            raise ValueError("unreviewed_verdict_forbidden")
        if reviewed != (self.review_provenance is not None) or reviewed != bool(self.conditions and self.branches):
            raise ValueError("invalid_preview_review_binding")
        expected_scope = {"bounded": "bounded_reviewed_synthesis", "branch_unresolved": "conditional_branches_only"}.get(self.review_status, "structure_only")
        if self.scope != expected_scope:
            raise ValueError("invalid_preview_scope")
        ids = {c.id for c in self.conditions}
        if len(ids) != len(self.conditions):
            raise ValueError("duplicate_conditions")
        refs = {r.evidence_id: r for r in self.classical_sources}
        for atom in [*self.conditions, *self.branches, *self.scope_limits]:
            if set(atom.source_evidence_ids) != {q.evidence_id for q in atom.source_quotes}:
                raise ValueError("invalid_public_source_binding")
            for q in atom.source_quotes:
                if q.evidence_id not in refs or q.quote not in refs[q.evidence_id].text:
                    raise ValueError("public_quote_unsupported")
        for branch in self.branches:
            if not branch.condition_ids or not set(branch.condition_ids) <= ids:
                raise ValueError("public_condition_unsupported")
        return self


class PreviewResponse(PublicModel):
    preview_api_version: Literal["traditional_preview_api_v1"]
    reading: ReadingResponse
    judgement: JudgementView
