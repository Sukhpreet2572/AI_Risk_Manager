from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    SUPERVISOR = "supervisor"
    TARGET = "target"


class ConversationMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    id: str
    scenario_title: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IssueType(str, Enum):
    HALLUCINATION = "hallucination"
    INCORRECT_INFORMATION = "incorrect_information"
    POLICY_VIOLATION = "policy_violation"
    UNSUPPORTED_PROMISE = "unsupported_promise"
    POOR_CUSTOMER_HANDLING = "poor_customer_handling"
    OTHER = "other"


class EvaluationIssue(BaseModel):
    issue_type: IssueType
    description: str
    severity: str = "medium"  # low, medium, high, critical


class EvaluationResult(BaseModel):
    scenario: str
    conversation_id: str
    score: float = Field(ge=0.0, le=10.0, description="Score out of 10")
    is_passed: bool
    detected_issues: List[EvaluationIssue] = Field(default_factory=list)
    explanation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str = "ok"
    project: str = "VocalChaos"


class ChatRequest(BaseModel):
    message: str = Field(..., description="Customer message input")
    conversation_id: Optional[str] = Field(default="default_session", description="Session conversation ID")


class ChatResponse(BaseModel):
    response: str
    agent: str = "target"
    conversation_id: str


class ResetResponse(BaseModel):
    status: str = "ok"
    message: str = "Conversation history cleared"
    conversation_id: str


class ScenarioInfo(BaseModel):
    id: str
    title: str
    objective: str
    starter_message: str


class SupervisorStartRequest(BaseModel):
    scenario_id: str = Field(default="refund_pressure", description="Scenario ID to begin")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation session ID")


class SupervisorStartResponse(BaseModel):
    scenario: str
    scenario_id: str
    message: str
    conversation_id: str


class SupervisorStepRequest(BaseModel):
    target_response: str = Field(..., description="Last response from Target Agent")
    scenario_id: str = Field(default="refund_pressure", description="Current scenario ID")
    conversation_id: Optional[str] = Field(default="default_supervisor_session", description="Conversation session ID")


class SupervisorStepResponse(BaseModel):
    supervisor_message: str
    conversation_id: str
    should_continue: bool = True


class ConversationTurn(BaseModel):
    role: str  # 'supervisor' or 'target'
    content: str
    turn_index: int


class SupervisorSimulateRequest(BaseModel):
    scenario_id: str = Field(default="refund_pressure", description="Scenario ID to simulate")
    max_turns: int = Field(default=4, ge=1, le=5, description="Maximum conversation turn pairs (max 5)")


class SupervisorSimulateResponse(BaseModel):
    scenario: str
    scenario_id: str
    conversation_id: str
    conversation: List[ConversationTurn]
    turns: int
    status: str = "completed"


class CategoryEvaluation(BaseModel):
    score: float = Field(ge=0.0, le=2.0, description="Score between 0 and 2")
    max_score: float = 2.0
    reason: str


class CategoryBreakdown(BaseModel):
    hallucination_resistance: CategoryEvaluation
    policy_compliance: CategoryEvaluation
    unsupported_promises: CategoryEvaluation
    missing_information: CategoryEvaluation
    professionalism: CategoryEvaluation


class DetailedIssue(BaseModel):
    type: str  # HALLUCINATION, POLICY_VIOLATION, UNSUPPORTED_PROMISE, MISSING_INFORMATION, UNVERIFIED_CLAIM_ACCEPTANCE, UNPROFESSIONAL_RESPONSE
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    evidence: str  # Exact quote from Target Agent
    why_it_is_wrong: str  # Explanation of failure
    relevant_policy_rule: Optional[str] = None


class TestContextInfo(BaseModel):
    what_was_tested: str
    attack_type: str
    target_response_audit: str
    knowledge_base_rule: str
    detected_failure: str


class EvaluateRequest(BaseModel):
    scenario_id: str = Field(default="refund_pressure", description="Scenario ID that was tested")
    conversation: List[ConversationTurn] = Field(..., description="Full list of turns in the conversation")


class EvaluateResponse(BaseModel):
    scenario: str
    scenario_id: str
    overall_score: float = Field(ge=0.0, le=10.0)
    result: str  # EXCELLENT, PASSED, WARNING, FAILED, CRITICAL FAILURE, FAILED — CRITICAL ISSUE
    critical_failure: bool = False
    categories: CategoryBreakdown
    issues: List[DetailedIssue] = Field(default_factory=list)
    summary: str
    test_context: TestContextInfo




