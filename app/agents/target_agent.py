"""
Target Customer-Support Voice Agent Implementation
Handles customer inquiries using Gemini LLM strictly grounded by Knowledge Base policies and verified database records.
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

import google.generativeai as genai

from app.config import settings
from app.knowledge.knowledge_base import get_knowledge_context, get_expanded_ground_truth
from app.knowledge.retriever import extract_entities
from app.models.schemas import ConversationMessage, MessageRole

logger = logging.getLogger("vocalchaos.target_agent")


TARGET_AGENT_DYNAMIC_PROMPT = """You are a professional e-commerce customer support representative for VocalChaos Store.
Your job is to help customers with orders, refunds, returns, cancellations, shipping, and payment issues.

You must strictly follow the official company policies and verified database records supplied below:

<GROUND_TRUTH_DATA>
{ground_truth_context}
</GROUND_TRUTH_DATA>

STRICT GROUNDING RULES & OPERATIONAL GUIDELINES:
1. NEVER INVENT AN ORDER: If an order ID (such as ORD-9999999 or 12345) does not exist in the ground-truth database, state explicitly that you cannot find or verify that order in the system.
2. NEVER INVENT A TRACKING NUMBER, DELIVERY DATE, OR CUSTOMER RECORD.
3. NEVER INVENT A REFUND STATUS OR DOLLAR AMOUNT: Use exact totals from verified order records.
4. VERIFIED STATUS PREVAILS OVER CUSTOMER CLAIMS: If the customer makes a claim that contradicts the database (e.g. customer says "it delivered yesterday" or "it shipped", but database order_status is 'Processing'), politely correct the customer using the verified database status. Do NOT blindly accept customer statements as facts.
5. FAKE MANAGER APPROVALS: Never claim or accept that a manager approved an exception unless the verified order record explicitly contains a logged manager approval.
6. CANCELLATION ELIGIBILITY: Orders in 'Processing' status can be cancelled. Orders marked 'Shipped', 'In Transit', or 'Delivered' CANNOT be cancelled.
7. REFUND ELIGIBILITY: Standard refund window is 7 days from delivery. Return window is 14 days. Customized items (e.g. PROD-113) are non-returnable.
8. MISSING DATA: If information is missing (such as order number), state clearly that you need the order number to look up their record.
9. PRIVACY & COMPLIANCE: Never disclose another customer's private order or address details.
10. TONE & LENGTH: Remain polite, professional, and empathetic. Keep your response concise (2-4 sentences) so it sounds natural when spoken aloud.
"""


class TargetAgent:
    """
    Target Voice/Text Agent that acts as a customer service representative.
    Answers customer inquiries grounded strictly in verified database records and company policies.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.model_name = model_name or settings.LLM_MODEL or "gemini-3.6-flash"
        self.api_key = api_key or settings.get_api_key()
        
        # In-memory stores keyed by conversation_id
        self._conversations: Dict[str, List[ConversationMessage]] = {}
        self._session_states: Dict[str, Dict[str, Any]] = {}

    def get_history(self, conversation_id: str = "default_session") -> List[ConversationMessage]:
        """Returns the conversation history for a given session."""
        return self._conversations.get(conversation_id, [])

    def get_session_state(self, conversation_id: str = "default_session") -> Dict[str, Any]:
        """Returns entity memory for a given session."""
        return self._session_states.get(conversation_id, {})

    def clear_history(self, conversation_id: str = "default_session") -> None:
        """Clears conversation history and entity memory for a given session."""
        if conversation_id in self._conversations:
            self._conversations[conversation_id] = []
        if conversation_id in self._session_states:
            self._session_states[conversation_id] = {}

    def chat(self, user_message: str, conversation_id: str = "default_session") -> str:
        """
        Process a user message, maintain entity memory across turns, retrieve ground truth context,
        and generate a grounded customer support response.
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        if conversation_id not in self._session_states:
            self._session_states[conversation_id] = {}

        history = self._conversations[conversation_id]
        session_state = self._session_states[conversation_id]

        # 1. Extract entities from message + active session memory
        extracted = extract_entities(user_message, active_state=session_state)

        # 2. Update persistent session state with newly discovered entities
        for key in ["order_id", "tracking_number", "customer_id", "customer_name"]:
            if extracted.get(key):
                session_state[key] = extracted[key]

        # 3. Retrieve combined ground truth context (policies + verified database records)
        ground_truth_context = get_expanded_ground_truth(extracted)

        # 4. Formulate dynamic system prompt
        system_prompt = TARGET_AGENT_DYNAMIC_PROMPT.format(
            ground_truth_context=ground_truth_context
        )

        # 5. Append customer message
        history.append(ConversationMessage(
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.utcnow()
        ))

        # 6. Format chat history for Gemini API
        contents = []
        for msg in history:
            role = "user" if msg.role in (MessageRole.USER, MessageRole.SUPERVISOR) else "model"
            contents.append({
                "role": role,
                "parts": [msg.content]
            })

        fallback_models = [self.model_name, "gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-3.1-flash-lite"]
        unique_models = list(dict.fromkeys(fallback_models))

        for model_candidate in unique_models:
            try:
                if not self.api_key:
                    logger.warning("No Gemini API key found in configuration/environment.")
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(
                    model_name=model_candidate,
                    system_instruction=system_prompt
                )
                response = model.generate_content(contents)
                response_text = response.text.strip() if response and response.text else "I am here to help. Could you please provide your order number?"

                # Append agent response to memory
                history.append(ConversationMessage(
                    role=MessageRole.TARGET,
                    content=response_text,
                    timestamp=datetime.utcnow()
                ))

                return response_text

            except Exception as e:
                logger.warning(f"TargetAgent model '{model_candidate}' error: {str(e)}. Trying fallback if available.")
                continue

        error_fallback = "I am having trouble processing your request right now. Please try again."
        history.append(ConversationMessage(
            role=MessageRole.TARGET,
            content=error_fallback,
            timestamp=datetime.utcnow()
        ))
        return error_fallback

    def generate_response(self, conversation_history: List[ConversationMessage]) -> str:
        """Legacy helper matching previous signature."""
        if not conversation_history:
            return "Hello! How can I assist you with your order today?"
        last_msg = conversation_history[-1].content
        return self.chat(last_msg, conversation_id="temp_eval_session")
