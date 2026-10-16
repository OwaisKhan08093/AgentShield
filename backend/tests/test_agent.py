"""Unit tests for deterministic ReferenceAgent and structured execution traces."""

import pytest
from app.agent import ReferenceAgent
from app.models import (
    AgentResponse,
    Customer,
    ExecutionStatus,
    ExecutionTrace,
    Order,
    SupportAction,
    SupportRequest,
    TraceEventType,
)
from app.security import AuthorizationGuard
from app.tools import SupportTools


# ==============================================================================
# 1. Authorized Success Paths
# ==============================================================================

def test_reference_agent_alice_order_lookup_success(reference_agent: ReferenceAgent):
    """Verify Alice can look up her own order A-100 via the reference agent."""
    request = SupportRequest(
        customer_id="alice",
        action="lookup_order",
        order_id="A-100",
    )
    response = reference_agent.execute(request)

    assert isinstance(response, AgentResponse)
    assert response.status == ExecutionStatus.SUCCESS
    assert response.is_success is True
    assert response.is_denied is False
    assert response.is_error is False
    assert response.data is not None
    assert response.data["order_id"] == "A-100"
    assert response.data["customer_id"] == "alice"
    assert response.data["status"] == "shipped"
    assert response.data["total_amount"] == 129.99

    # Verify Trace structure and sequence
    trace = response.trace
    assert isinstance(trace, ExecutionTrace)
    assert trace.execution_id == response.execution_id
    assert trace.customer_id == "alice"
    assert trace.action == "lookup_order"
    assert trace.status == ExecutionStatus.SUCCESS
    assert len(trace.events) == 4

    # Event 1: Request
    assert trace.events[0].sequence == 1
    assert trace.events[0].event_type == TraceEventType.REQUEST
    assert trace.events[0].sanitized_payload["order_id"] == "A-100"

    # Event 2: Tool Call
    assert trace.events[1].sequence == 2
    assert trace.events[1].event_type == TraceEventType.TOOL_CALL
    assert trace.events[1].tool_name == "lookup_order"

    # Event 3: Tool Result
    assert trace.events[2].sequence == 3
    assert trace.events[2].event_type == TraceEventType.TOOL_RESULT
    assert trace.events[2].tool_name == "lookup_order"
    assert trace.events[2].is_denied is False

    # Event 4: Response
    assert trace.events[3].sequence == 4
    assert trace.events[3].event_type == TraceEventType.RESPONSE
    assert trace.events[3].decision == "success"


def test_reference_agent_bob_order_lookup_success(reference_agent: ReferenceAgent):
    """Verify Bob can look up his own order B-200 via the reference agent."""
    request = SupportRequest(
        customer_id="bob",
        action=SupportAction.LOOKUP_ORDER,
        order_id="B-200",
    )
    response = reference_agent.execute(request)

    assert response.status == ExecutionStatus.SUCCESS
    assert response.data["order_id"] == "B-200"
    assert response.data["customer_id"] == "bob"
    assert response.trace.status == ExecutionStatus.SUCCESS


def test_reference_agent_refund_policy_success(reference_agent: ReferenceAgent):
    """Verify refund policy lookup via the reference agent."""
    request = SupportRequest(
        action="get_refund_policy",
        category="electronics",
    )
    response = reference_agent.execute(request)

    assert response.status == ExecutionStatus.SUCCESS
    assert response.data is not None
    assert response.data["window_days"] == 30
    assert response.data["requested_category"] == "electronics"
    assert response.trace.status == ExecutionStatus.SUCCESS


def test_reference_agent_valid_refund_approval_request(reference_agent: ReferenceAgent):
    """Verify creating a simulated refund approval request via reference agent."""
    request = SupportRequest(
        customer_id="alice",
        action="request_refund_approval",
        order_id="A-100",
        amount=50.0,
        reason="Defective item",
    )
    response = reference_agent.execute(request)

    assert response.status == ExecutionStatus.SUCCESS
    assert response.data is not None
    assert response.data["order_id"] == "A-100"
    assert response.data["requested_amount"] == 50.0
    assert response.data["status"] == "simulated_approval_pending"
    assert "SIMULATION ONLY" in response.data["simulation_notice"]
    assert response.trace.status == ExecutionStatus.SUCCESS


# ==============================================================================
# 2. Unauthorized Operations and Zero Data Leakage
# ==============================================================================

def test_reference_agent_alice_lookup_bob_order_denied(
    reference_agent: ReferenceAgent,
    bob_customer: Customer,
    order_b200: Order,
):
    """Verify Alice looking up Bob's order is denied and zero Bob data leaks into trace."""
    request = SupportRequest(
        customer_id="alice",
        action="lookup_order",
        order_id="B-200",
    )
    response = reference_agent.execute(request)

    assert response.status == ExecutionStatus.DENIED
    assert response.is_denied is True
    assert response.data is None
    assert "denied" in response.summary.lower()

    # Inspect the execution trace
    trace = response.trace
    assert trace.status == ExecutionStatus.DENIED
    assert trace.final_result is None

    # Check that denial flag is recorded on tool result event
    tool_result_evt = next(e for e in trace.events if e.event_type == TraceEventType.TOOL_RESULT)
    assert tool_result_evt.is_denied is True
    assert tool_result_evt.decision == "denied"

    # Serialize entire trace to string to verify zero data leakage
    trace_dump_str = trace.model_dump_json().lower()
    assert "bob jones" not in trace_dump_str
    assert bob_customer.email.lower() not in trace_dump_str
    for item in order_b200.items:
        assert item.lower() not in trace_dump_str
    if order_b200.notes:
        assert order_b200.notes.lower() not in trace_dump_str


def test_reference_agent_bob_lookup_alice_order_denied(
    reference_agent: ReferenceAgent,
    alice_customer: Customer,
    order_a100: Order,
):
    """Verify Bob looking up Alice's order is denied and zero Alice data leaks into trace."""
    request = SupportRequest(
        customer_id="bob",
        action="lookup_order",
        order_id="A-100",
    )
    response = reference_agent.execute(request)

    assert response.status == ExecutionStatus.DENIED
    assert response.is_denied is True
    assert response.data is None

    trace_dump_str = response.trace.model_dump_json().lower()
    assert "alice smith" not in trace_dump_str
    assert alice_customer.email.lower() not in trace_dump_str
    for item in order_a100.items:
        assert item.lower() not in trace_dump_str
    if order_a100.notes:
        assert order_a100.notes.lower() not in trace_dump_str


def test_reference_agent_unauthorized_refund_approval_denied(reference_agent: ReferenceAgent):
    """Verify Alice cannot request a refund for Bob's order B-200."""
    request = SupportRequest(
        customer_id="alice",
        action="request_refund_approval",
        order_id="B-200",
        amount=50.0,
        reason="Malicious refund attempt",
    )
    response = reference_agent.execute(request)

    assert response.status == ExecutionStatus.DENIED
    assert response.is_denied is True
    assert response.data is None
    assert response.trace.status == ExecutionStatus.DENIED


# ==============================================================================
# 3. Invalid Actions, Malformed Inputs, and Edge Cases
# ==============================================================================

def test_reference_agent_unsupported_action(reference_agent: ReferenceAgent):
    """Verify reference agent returns error status for unsupported actions."""
    request = SupportRequest(
        customer_id="alice",
        action="format_hard_drive",
        order_id="A-100",
    )
    response = reference_agent.execute(request)

    assert response.status == ExecutionStatus.ERROR
    assert response.is_error is True
    assert response.data is None
    assert "unsupported" in response.summary.lower()


def test_reference_agent_dict_input_support(reference_agent: ReferenceAgent):
    """Verify execute() accepts raw dictionary input matching SupportRequest."""
    raw_dict = {
        "customer_id": "alice",
        "action": "lookup_order",
        "order_id": "A-100",
    }
    response = reference_agent.execute(raw_dict)
    assert response.status == ExecutionStatus.SUCCESS
    assert response.data["order_id"] == "A-100"


def test_reference_agent_malformed_dict_input(reference_agent: ReferenceAgent):
    """Verify execute() handles invalid dictionary input safely without raising."""
    raw_dict = {
        "customer_id": "alice",
        # missing action field
        "order_id": "A-100",
    }
    response = reference_agent.execute(raw_dict)
    assert response.status == ExecutionStatus.ERROR
    assert response.data is None
    assert "invalid" in response.summary.lower()


def test_reference_agent_invalid_input_type(reference_agent: ReferenceAgent):
    """Verify execute() handles non-dict, non-SupportRequest inputs safely."""
    response = reference_agent.execute(["invalid", "input", "list"])  # type: ignore[arg-type]
    assert response.status == ExecutionStatus.ERROR
    assert response.data is None


def test_reference_agent_refund_amount_exceeding_total(reference_agent: ReferenceAgent):
    """Verify refund request exceeding total order amount produces error."""
    request = SupportRequest(
        customer_id="alice",
        action="request_refund_approval",
        order_id="A-100",
        amount=999.99,  # Order total is 129.99
    )
    response = reference_agent.execute(request)
    assert response.status == ExecutionStatus.ERROR
    assert response.data is None
    assert "exceeds order total" in response.summary.lower()


# ==============================================================================
# 4. Fail-Closed Error Handling on Tool Exceptions
# ==============================================================================

def test_reference_agent_fails_closed_on_tool_exception():
    """Verify agent fails closed when a tool throws an unhandled exception."""
    class BrokenTools(SupportTools):
        def lookup_order(self, customer_id, order_id):
            raise RuntimeError("Hardware failure simulation")

    guard = AuthorizationGuard(orders={}, customers={})
    agent = ReferenceAgent(BrokenTools(guard))

    request = SupportRequest(
        customer_id="alice",
        action="lookup_order",
        order_id="A-100",
    )
    response = agent.execute(request)

    assert response.status == ExecutionStatus.ERROR
    assert response.is_error is True
    assert response.data is None
    assert response.trace.status == ExecutionStatus.ERROR


# ==============================================================================
# 5. Trace Ordering, Identifiers, and Serialization
# ==============================================================================

def test_execution_trace_ordering_and_identifiers(reference_agent: ReferenceAgent):
    """Verify trace events have strict chronological sequence and unique IDs."""
    request = SupportRequest(
        customer_id="alice",
        action="lookup_order",
        order_id="A-100",
    )
    response = reference_agent.execute(request)
    trace = response.trace

    assert trace.execution_id.startswith("exec_")
    sequences = [evt.sequence for evt in trace.events]
    assert sequences == list(range(1, len(trace.events) + 1))

    event_ids = [evt.event_id for evt in trace.events]
    assert len(event_ids) == len(set(event_ids)), "Event IDs must be unique"
    for eid in event_ids:
        assert eid.startswith("evt_")


def test_trace_and_response_serialization_roundtrip(reference_agent: ReferenceAgent):
    """Verify AgentResponse and ExecutionTrace serialize and deserialize cleanly."""
    request = SupportRequest(
        customer_id="alice",
        action="lookup_order",
        order_id="A-100",
    )
    response = reference_agent.execute(request)

    # Dump to dict
    response_dict = response.model_dump()
    reconstituted = AgentResponse.model_validate(response_dict)
    assert reconstituted == response

    # Dump to JSON
    response_json = response.model_dump_json()
    assert isinstance(response_json, str)
    reconstituted_from_json = AgentResponse.model_validate_json(response_json)
    assert reconstituted_from_json == response
