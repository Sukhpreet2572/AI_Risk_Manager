import logging
import uuid
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import (
    HealthResponse,
    ChatRequest,
    ChatResponse,
    ResetResponse,
    ConversationMessage,
    MessageRole,
    ScenarioInfo,
    SupervisorStartRequest,
    SupervisorStartResponse,
    SupervisorStepRequest,
    SupervisorStepResponse,
    SupervisorSimulateRequest,
    SupervisorSimulateResponse,
    ConversationTurn,
    EvaluateRequest,
    EvaluateResponse,
)
from app.agents.target_agent import TargetAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.evaluation.evaluator import Evaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vocalchaos.api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)

# Enable CORS for local Streamlit UI and browser speech components
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent & Evaluator instances
target_agent = TargetAgent()
supervisor_agent = SupervisorAgent()
evaluator = Evaluator()


# ==================== Health & Root Endpoints ====================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health() -> HealthResponse:
    """Health check endpoint returning system status and project identifier."""
    return HealthResponse(
        status="ok",
        project="VocalChaos"
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "description": settings.PROJECT_DESCRIPTION,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "POST /chat",
            "reset": "POST /reset",
            "history": "GET /history/{conversation_id}",
            "supervisor_scenarios": "GET /supervisor/scenarios",
            "supervisor_start": "POST /supervisor/start",
            "supervisor_step": "POST /supervisor/step",
            "supervisor_simulate": "POST /supervisor/simulate",
            "evaluate": "POST /evaluate"
        }
    }


# ==================== Target Agent Endpoints ====================

@app.post("/chat", response_model=ChatResponse, tags=["Target Agent"])
async def chat_with_target_agent(request: ChatRequest) -> ChatResponse:
    """
    Send a customer query to the Target Voice Agent and receive a response strictly bounded by knowledge base.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conv_id = request.conversation_id or "default_session"
    logger.info(f"Received message for session '{conv_id}': {request.message}")

    agent_response = target_agent.chat(
        user_message=request.message.strip(),
        conversation_id=conv_id
    )

    return ChatResponse(
        response=agent_response,
        agent="target",
        conversation_id=conv_id
    )


@app.post("/reset", response_model=ResetResponse, tags=["Target Agent"])
async def reset_conversation(conversation_id: str = "default_session") -> ResetResponse:
    """Reset and clear conversation memory for a given session."""
    target_agent.clear_history(conversation_id)
    return ResetResponse(
        status="ok",
        message="Conversation history cleared",
        conversation_id=conversation_id
    )


@app.get("/history/{conversation_id}", response_model=List[ConversationMessage], tags=["Target Agent"])
async def get_conversation_history(conversation_id: str) -> List[ConversationMessage]:
    """Retrieve message history for a specific conversation session."""
    return target_agent.get_history(conversation_id)


# ==================== Supervisor Agent Endpoints ====================

@app.get("/supervisor/scenarios", response_model=List[ScenarioInfo], tags=["Supervisor Agent"])
async def list_scenarios() -> List[ScenarioInfo]:
    """List all available stress-test scenarios."""
    scenarios = supervisor_agent.list_scenarios()
    return [
        ScenarioInfo(
            id=s["id"],
            title=s["title"],
            objective=s["objective"],
            starter_message=s["starter_message"]
        )
        for s in scenarios
    ]


@app.post("/supervisor/start", response_model=SupervisorStartResponse, tags=["Supervisor Agent"])
async def supervisor_start(request: SupervisorStartRequest) -> SupervisorStartResponse:
    """
    Start a supervisor stress-test session with the initial customer message for the given scenario.
    """
    scenario = supervisor_agent.get_scenario(request.scenario_id)
    conv_id = request.conversation_id or f"test_{uuid.uuid4().hex[:8]}"
    
    # Initialize/clear target agent memory for this test session
    target_agent.clear_history(conv_id)
    
    starter_msg = scenario["starter_message"]
    return SupervisorStartResponse(
        scenario=scenario["title"],
        scenario_id=scenario["id"],
        message=starter_msg,
        conversation_id=conv_id
    )


@app.post("/supervisor/step", response_model=SupervisorStepResponse, tags=["Supervisor Agent"])
async def supervisor_step(request: SupervisorStepRequest) -> SupervisorStepResponse:
    """
    Generate the next tricky customer turn based on Target Agent's response and conversation history.
    """
    conv_id = request.conversation_id or "default_supervisor_session"
    history = target_agent.get_history(conv_id)
    
    next_customer_turn = supervisor_agent.generate_turn(
        scenario_id=request.scenario_id,
        conversation_history=history
    )
    
    return SupervisorStepResponse(
        supervisor_message=next_customer_turn,
        conversation_id=conv_id,
        should_continue=len(history) < 10
    )


@app.post("/supervisor/simulate", response_model=SupervisorSimulateResponse, tags=["Supervisor Agent"])
async def supervisor_simulate(request: SupervisorSimulateRequest) -> SupervisorSimulateResponse:
    """
    Run an automated multi-turn stress test simulation between Supervisor Agent and Target Agent.
    Maximum: 5 turns (turn pairs).
    """
    scenario = supervisor_agent.get_scenario(request.scenario_id)
    conv_id = f"sim_{scenario['id']}_{uuid.uuid4().hex[:6]}"
    max_turns = min(max(1, request.max_turns), 5)

    target_agent.clear_history(conv_id)
    conversation_turns: List[ConversationTurn] = []

    logger.info(f"Starting simulation for scenario '{scenario['title']}' with {max_turns} turns (session {conv_id})")

    # Turn 1: Starter message from supervisor
    current_customer_msg = scenario["starter_message"]

    for turn_idx in range(1, max_turns + 1):
        # 1. Record Supervisor turn
        conversation_turns.append(ConversationTurn(
            role="supervisor",
            content=current_customer_msg,
            turn_index=turn_idx
        ))

        # 2. Target Agent processes message and responds
        target_reply = target_agent.chat(
            user_message=current_customer_msg,
            conversation_id=conv_id
        )

        # 3. Record Target Agent response
        conversation_turns.append(ConversationTurn(
            role="target",
            content=target_reply,
            turn_index=turn_idx
        ))

        # If not the last turn, generate next adversarial customer turn from Supervisor
        if turn_idx < max_turns:
            history = target_agent.get_history(conv_id)
            current_customer_msg = supervisor_agent.generate_turn(
                scenario_id=scenario["id"],
                conversation_history=history
            )

    return SupervisorSimulateResponse(
        scenario=scenario["title"],
        scenario_id=scenario["id"],
        conversation_id=conv_id,
        conversation=conversation_turns,
        turns=max_turns,
        status="completed"
    )


# ==================== Automated Evaluator Endpoint ====================

@app.post("/evaluate", response_model=EvaluateResponse, tags=["Evaluation"])
async def evaluate_conversation(request: EvaluateRequest) -> EvaluateResponse:
    """
    Audit and evaluate a completed conversation transcript against policies and scenario objectives.
    """
    if not request.conversation:
        raise HTTPException(status_code=400, detail="Conversation turns cannot be empty for evaluation")

    logger.info(f"Auditing conversation ({len(request.conversation)} turns) for scenario '{request.scenario_id}'")

    raw_turns = [
        {"role": turn.role, "content": turn.content, "turn_index": turn.turn_index}
        for turn in request.conversation
    ]

    evaluation_response = evaluator.evaluate_transcript(
        scenario_id=request.scenario_id,
        conversation_turns=raw_turns
    )

    return evaluation_response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
