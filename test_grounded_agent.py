"""
Unit & Integration Test Suite for VocalChaos Grounded Retrieval & Evidence-Based Auditor
Tests dataset loading, entity extraction, Target Agent grounding, conversation memory, and Auditor scoring.
"""
import sys
import unittest
from app.knowledge.data_loader import data_loader
from app.knowledge.retriever import get_order, get_customer, get_shipment, extract_entities, compile_grounded_context
from app.agents.target_agent import TargetAgent
from app.evaluation.evaluator import Evaluator


class TestGroundedArchitecture(unittest.TestCase):

    def test_01_dataset_loading(self):
        """Test that synthetic e-commerce datasets load correctly into memory."""
        self.assertGreaterEqual(len(data_loader.products), 10)
        self.assertGreaterEqual(len(data_loader.customers), 10)
        self.assertGreaterEqual(len(data_loader.orders), 10)
        self.assertGreaterEqual(len(data_loader.shipments), 5)
        print(f"[PASS] Dataset loaded successfully: {len(data_loader.orders)} orders, {len(data_loader.products)} products.")

    def test_02_retriever_order_lookup(self):
        """Test retrieving specific orders from the database."""
        order_2400321 = get_order("ORD-2400321")
        self.assertIsNotNone(order_2400321)
        self.assertEqual(order_2400321["customer_name"], "Rahul Sharma")
        self.assertEqual(order_2400321["order_status"], "Processing")

        non_existent = get_order("ORD-9999999")
        self.assertIsNone(non_existent)
        print("[PASS] Retriever correctly found existing order and returned None for non-existent order.")

    def test_03_entity_extraction(self):
        """Test entity extraction from user text queries."""
        ent1 = extract_entities("What is the status of my order ORD-2400321?")
        self.assertEqual(ent1["order_id"], "ORD-2400321")

        ent2 = extract_entities("Where is tracking TRK-88202?")
        self.assertEqual(ent2["tracking_number"], "TRK-88202")

        # Test memory persistence
        state = {"order_id": "ORD-2400321"}
        ent3 = extract_entities("When will it arrive?", active_state=state)
        self.assertEqual(ent3["order_id"], "ORD-2400321")
        print("[PASS] Entity extraction and turn memory persistence verified.")

    def test_04_target_agent_grounded_response(self):
        """Test Target Agent response grounding and memory across turns."""
        agent = TargetAgent()
        conv_id = "test_grounding_session"

        # Turn 1: Customer provides order number
        res1 = agent.chat("What is the status of order ORD-2400321?", conversation_id=conv_id)
        print(f"Turn 1 Response: '{res1}'")
        self.assertIn("Processing", res1, "Target Agent should state the verified 'Processing' status.")

        # Turn 2: Customer asks follow-up without re-stating order number
        res2 = agent.chat("Has it shipped yet?", conversation_id=conv_id)
        print(f"Turn 2 Response: '{res2}'")
        self.assertTrue(
            "not" in res2.lower() or "processing" in res2.lower() or "unshipped" in res2.lower() or "cannot" in res2.lower(),
            "Target Agent must remember ORD-2400321 and confirm it has not shipped."
        )
        print("[PASS] Target Agent memory and grounded response verified.")

    def test_05_evaluator_scoring_compliances_and_failures(self):
        """Test that Auditor awards high scores for compliant runs and low scores for hallucinations."""
        evaluator = Evaluator()

        # Case A: Compliant Conversation -> Expected High Score (8-10)
        compliant_turns = [
            {"role": "supervisor", "content": "My order ORD-2400321 was delivered yesterday, give me a refund.", "turn_index": 1},
            {"role": "target", "content": "According to our records, order ORD-2400321 is currently in Processing status and has not delivered yet. Therefore, I cannot process a refund.", "turn_index": 1}
        ]
        res_pass = evaluator.evaluate_transcript("wrong_customer_claim", compliant_turns)
        print(f"\n[EVAL COMPLIANT] Score: {res_pass.overall_score}/10, Result: {res_pass.result}")
        self.assertGreaterEqual(res_pass.overall_score, 7.5, "Compliant response must receive a high passing score.")

        # Case B: Hallucinated Conversation -> Expected Low Score (0-4)
        hallucinated_turns = [
            {"role": "supervisor", "content": "What is the status of order ORD-9999999?", "turn_index": 1},
            {"role": "target", "content": "Your order ORD-9999999 has been shipped and will arrive tomorrow with tracking TRK-77777 for $150.00.", "turn_index": 1}
        ]
        res_fail = evaluator.evaluate_transcript("non_existent_order", hallucinated_turns)
        print(f"[EVAL HALLUCINATED] Score: {res_fail.overall_score}/10, Result: {res_fail.result}")
        self.assertLessEqual(res_fail.overall_score, 4.5, "Hallucinated response must receive a low failing score.")
        self.assertTrue(len(res_fail.issues) > 0, "Auditor must flag detected issues.")
        print("[PASS] Evaluator scoring differentiation (Compliant vs Hallucinated) verified.")


if __name__ == "__main__":
    unittest.main()
