import re
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class ActionableDeepLink(BaseModel):
    id: str = Field(..., description="Unique deep link identifier")
    step_number: int = Field(..., ge=1, description="1-indexed sequence order")
    title: str = Field(..., description="2 to 3 words in sentence case")
    description: str = Field(..., description="Exactly 5 to 7 words starting with 'It will...'")
    uri: str = Field(..., description="Strictly bixby:// URI")
    is_destructive: bool = Field(default=False, description="Flag for destructive operations")
    invasive_level: int = Field(default=1, ge=1, le=3, description="1=safe toggle, 2=moderate/cache, 3=destructive")
    action_type: str = Field(default="toggle", description="toggle, clear, navigation, slider, or reset")

    @field_validator("title")
    @classmethod
    def validate_title_syntax(cls, v: str) -> str:
        v = v.strip()
        words = v.split()
        if len(words) not in (2, 3):
            raise ValueError(f"Title must be exactly 2 or 3 words. Got {len(words)} words: '{v}'")
        if not words[0][0].isupper():
            raise ValueError(f"Title must be in sentence case (first letter capitalized): '{v}'")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_syntax(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("It will"):
            raise ValueError(f"Description must start with 'It will...': Got '{v}'")
        # Strip trailing dot for word count
        clean_v = v.rstrip(".")
        words = clean_v.split()
        if len(words) not in (5, 6, 7):
            raise ValueError(f"Description must be exactly 5 to 7 words. Got {len(words)}: '{v}'")
        return v

    @field_validator("uri")
    @classmethod
    def validate_uri_zero_web_leak(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("bixby://"):
            raise ValueError(f"URI must strictly start with 'bixby://'. Got '{v}'")
        forbidden = ["http://", "https://", "www.", ".com", ".org", ".net", "markdown", "[", "]"]
        for leak in forbidden:
            if leak in v.lower():
                raise ValueError(f"Zero Web URL Leaks rule violated! Forbidden token '{leak}' in URI '{v}'")
        return v


class ValidationDeepLink(BaseModel):
    title: str = Field(..., description="2 to 3 words in sentence case")
    description: str = Field(..., description="Exactly 5 to 7 words starting with 'It will...'")
    uri: str = Field(..., description="Verification bixby:// URI")
    expected_outcome: str = Field(..., description="Observable diagnostic state")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        words = v.strip().split()
        if len(words) not in (2, 3):
            raise ValueError(f"Title must be 2 or 3 words, got '{v}'")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip().startswith("It will"):
            raise ValueError(f"Description must start with 'It will': '{v}'")
        words = v.strip().rstrip(".").split()
        if len(words) not in (5, 6, 7):
            raise ValueError(f"Description must be 5-7 words, got {len(words)}: '{v}'")
        return v

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        if not v.strip().startswith("bixby://"):
            raise ValueError(f"URI must start with bixby://: '{v}'")
        return v


class StepGroup(BaseModel):
    group_id: str = Field(..., description="Unique group identifier")
    name: str = Field(..., description="Group label (e.g. Non-Invasive Toggles)")
    description: str = Field(..., description="Group operational purpose")
    step_numbers: List[int] = Field(..., description="Ordered list of step indices in this group")


class Action(BaseModel):
    step_number: int = Field(..., ge=1)
    instruction: str = Field(..., description="Step action instruction")
    deep_link: ActionableDeepLink
    safety_warning: Optional[str] = Field(default=None)


class ExecutionMetadata(BaseModel):
    latency_ms: float = Field(..., description="Execution latency in milliseconds")
    cache_hit: bool = Field(..., description="Fast-path cache hit status")
    model: str = Field(..., description="Engine model identification")
    cost_usd: float = Field(..., ge=0.0, description="Inference cost in USD")


class TroubleshootRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User raw complaint or query")
    siis_response: Optional[str] = Field(default=None, description="Optional SIIS response context")


class TroubleshootResponse(BaseModel):
    goal: str = Field(..., description="Follow these steps to perform <Topic> Troubleshooting or Configuration")
    steps: List[ActionableDeepLink] = Field(default_factory=list, description="Ordered list of actionable deep links")
    step_groups: List[StepGroup] = Field(default_factory=list, description="Grouped diagnostic hierarchy")
    validation: Optional[ValidationDeepLink] = Field(default=None, description="Post-troubleshooting validation link")
    contexts: List[str] = Field(default_factory=list, description="Contextual search hits or empty on fallback")
    fallback: Optional[str] = Field(default=None, description="'no match' when no viable solution exists")
    meta: ExecutionMetadata

    @field_validator("goal")
    @classmethod
    def validate_goal_syntax(cls, v: str) -> str:
        pattern = r"^Follow these steps to perform .+ (Troubleshooting|Configuration)$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Goal must strictly follow 'Follow these steps to perform <Topic> Troubleshooting or Configuration'. Got '{v}'"
            )
        return v

    @model_validator(mode="after")
    def validate_safe_ordering_and_fallback(self):
        # Fallback check
        if self.fallback == "no match":
            if len(self.contexts) > 0:
                raise ValueError("When fallback is 'no match', contexts must be an empty list []")
            return self

        # Non-destructive first, destructive last ordering check
        if self.steps:
            seen_destructive = False
            for step in self.steps:
                if step.is_destructive or step.invasive_level == 3:
                    seen_destructive = True
                elif seen_destructive:
                    raise ValueError(
                        f"Unsafe plan ordering! Non-destructive step '{step.title}' (level {step.invasive_level}) "
                        f"appears after a destructive step."
                    )
        return self
