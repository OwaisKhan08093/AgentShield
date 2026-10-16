"""Deterministic reference customer-support agent with structured execution traces.

Executes rule-based routing for support actions, invoking SupportTools while
recording ordered, sanitized execution traces. Adheres to fail-closed principles
and never bypasses the tool authorization guard.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError

from app.agent.base import BaseAgent
from app.models import (
    AgentResponse,
    ExecutionStatus,
    ExecutionTrace,
    SupportRequest,
    ToolResultStatus,
    TraceEvent,
    TraceEventType,
)
from app.tools import SupportTools


class ReferenceAgent(BaseAgent):
    """Deterministic, rule-based AI agent representing reference support behavior."""

    def __init__(self, tools: SupportTools):
        """Initialize the reference agent with a SupportTools instance."""
        self.tools = tools

    def execute(self, request: Union[SupportRequest, Dict[str, Any]]) -> AgentResponse:
        """Process a support request deterministically and record an execution trace.

        Fails closed on malformed requests, unknown actions, tool errors, or authorization denials.
        """
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc).isoformat()
        events: List[TraceEvent] = []
        seq = 1

        # 1. Parse and validate input request
        parsed_request: Optional[SupportRequest] = None
        if isinstance(request, SupportRequest):
            parsed_request = request
        elif isinstance(request, dict):
            try:
                parsed_request = SupportRequest.model_validate(request)
            except ValidationError as val_err:
                error_event = TraceEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:8]}",
                    sequence=seq,
                    event_type=TraceEventType.RESPONSE,
                    decision="error",
                    is_denied=False,
                    sanitized_payload={"validation_error": str(val_err)},
                )
                events.append(error_event)
                completed_at = datetime.now(timezone.utc).isoformat()
                trace = ExecutionTrace(
                    execution_id=execution_id,
                    customer_id=request.get("customer_id") if isinstance(request, dict) else None,
                    action=str(request.get("action", "unknown")) if isinstance(request, dict) else "unknown",
                    status=ExecutionStatus.ERROR,
                    summary=f"Invalid support request format: {val_err.errors()[0].get('msg', 'validation error')}",
                    events=events,
                    final_result=None,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                return AgentResponse(
                    execution_id=execution_id,
                    status=ExecutionStatus.ERROR,
                    summary=trace.summary,
                    data=None,
                    trace=trace,
                )
        else:
            completed_at = datetime.now(timezone.utc).isoformat()
            summary = "Invalid support request: input must be a SupportRequest or dictionary."
            trace = ExecutionTrace(
                execution_id=execution_id,
                customer_id=None,
                action="invalid",
                status=ExecutionStatus.ERROR,
                summary=summary,
                events=[],
                final_result=None,
                started_at=started_at,
                completed_at=completed_at,
            )
            return AgentResponse(
                execution_id=execution_id,
                status=ExecutionStatus.ERROR,
                summary=summary,
                data=None,
                trace=trace,
            )

        # 2. Record initial request event
        req_payload: Dict[str, Any] = {
            "action": parsed_request.action,
            "customer_id": parsed_request.customer_id,
        }
        if parsed_request.order_id:
            req_payload["order_id"] = parsed_request.order_id
        if parsed_request.amount is not None:
            req_payload["amount"] = parsed_request.amount
        if parsed_request.category:
            req_payload["category"] = parsed_request.category

        events.append(
            TraceEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                sequence=seq,
                event_type=TraceEventType.REQUEST,
                decision="received",
                is_denied=False,
                sanitized_payload=req_payload,
            )
        )
        seq += 1

        action_normalized = parsed_request.action.lower().strip()
        final_status = ExecutionStatus.ERROR
        summary = "Unknown outcome."
        final_data: Optional[Dict[str, Any]] = None

        try:
            # 3. Deterministic tool routing
            if action_normalized in ("lookup_order", "lookup", "get_order"):
                tool_name = "lookup_order"
                events.append(
                    TraceEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:8]}",
                        sequence=seq,
                        event_type=TraceEventType.TOOL_CALL,
                        tool_name=tool_name,
                        decision="invoked",
                        is_denied=False,
                        sanitized_payload={
                            "customer_id": parsed_request.customer_id,
                            "order_id": parsed_request.order_id,
                        },
                    )
                )
                seq += 1

                tool_result = self.tools.lookup_order(
                    customer_id=parsed_request.customer_id,
                    order_id=parsed_request.order_id,
                )

                if tool_result.status == ToolResultStatus.SUCCESS:
                    final_status = ExecutionStatus.SUCCESS
                    summary = f"Order {parsed_request.order_id} successfully retrieved for customer {parsed_request.customer_id}."
                    final_data = tool_result.data
                    result_payload = tool_result.data
                elif tool_result.status == ToolResultStatus.DENIED:
                    final_status = ExecutionStatus.DENIED
                    summary = tool_result.error or "Access denied."
                    result_payload = {"denial_reason": tool_result.error}
                else:
                    final_status = ExecutionStatus.ERROR
                    summary = tool_result.error or "Error looking up order."
                    result_payload = {"error": tool_result.error}

                events.append(
                    TraceEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:8]}",
                        sequence=seq,
                        event_type=TraceEventType.TOOL_RESULT,
                        tool_name=tool_name,
                        decision=tool_result.status.value,
                        is_denied=tool_result.is_denied,
                        sanitized_payload=result_payload,
                    )
                )
                seq += 1

            elif action_normalized in ("get_refund_policy", "refund_policy", "policy"):
                tool_name = "get_refund_policy"
                events.append(
                    TraceEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:8]}",
                        sequence=seq,
                        event_type=TraceEventType.TOOL_CALL,
                        tool_name=tool_name,
                        decision="invoked",
                        is_denied=False,
                        sanitized_payload={"category": parsed_request.category or "general"},
                    )
                )
                seq += 1

                tool_result = self.tools.get_refund_policy(category=parsed_request.category)

                if tool_result.status == ToolResultStatus.SUCCESS:
                    final_status = ExecutionStatus.SUCCESS
                    summary = "Synthetic refund policy retrieved successfully."
                    final_data = tool_result.data
                    result_payload = tool_result.data
                else:
                    final_status = ExecutionStatus.ERROR
                    summary = tool_result.error or "Error retrieving refund policy."
                    result_payload = {"error": tool_result.error}

                events.append(
                    TraceEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:8]}",
                        sequence=seq,
                        event_type=TraceEventType.TOOL_RESULT,
                        tool_name=tool_name,
                        decision=tool_result.status.value,
                        is_denied=tool_result.is_denied,
                        sanitized_payload=result_payload,
                    )
                )
                seq += 1

            elif action_normalized in ("request_refund_approval", "refund_approval", "refund"):
                tool_name = "request_refund_approval"
                events.append(
                    TraceEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:8]}",
                        sequence=seq,
                        event_type=TraceEventType.TOOL_CALL,
                        tool_name=tool_name,
                        decision="invoked",
                        is_denied=False,
                        sanitized_payload={
                            "customer_id": parsed_request.customer_id,
                            "order_id": parsed_request.order_id,
                            "amount": parsed_request.amount,
                        },
                    )
                )
                seq += 1

                tool_result = self.tools.request_refund_approval(
                    customer_id=parsed_request.customer_id,
                    order_id=parsed_request.order_id,
                    amount=parsed_request.amount,
                    reason=parsed_request.reason,
                )

                if tool_result.status == ToolResultStatus.SUCCESS:
                    final_status = ExecutionStatus.SUCCESS
                    amount_str = f"{tool_result.amount:.2f}" if tool_result.amount is not None else "0.00"
                    summary = f"Simulated refund approval request created for order {parsed_request.order_id} (amount: {amount_str})."
                    final_data = tool_result.data
                    result_payload = tool_result.data
                elif tool_result.status == ToolResultStatus.DENIED:
                    final_status = ExecutionStatus.DENIED
                    summary = tool_result.error or "Access denied."
                    result_payload = {"denial_reason": tool_result.error}
                else:
                    final_status = ExecutionStatus.ERROR
                    summary = tool_result.error or "Refund approval request error."
                    result_payload = {"error": tool_result.error}

                events.append(
                    TraceEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:8]}",
                        sequence=seq,
                        event_type=TraceEventType.TOOL_RESULT,
                        tool_name=tool_name,
                        decision=tool_result.status.value,
                        is_denied=tool_result.is_denied,
                        sanitized_payload=result_payload,
                    )
                )
                seq += 1

            else:
                final_status = ExecutionStatus.ERROR
                summary = f"Unknown or unsupported support action: '{parsed_request.action}'."

        except Exception as exc:
            final_status = ExecutionStatus.ERROR
            summary = "Agent execution failed due to an unexpected internal error."
            events.append(
                TraceEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:8]}",
                    sequence=seq,
                    event_type=TraceEventType.RESPONSE,
                    decision="error",
                    is_denied=False,
                    sanitized_payload={"exception": type(exc).__name__},
                )
            )
            seq += 1

        # 4. Final response trace event
        events.append(
            TraceEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                sequence=seq,
                event_type=TraceEventType.RESPONSE,
                decision=final_status.value,
                is_denied=(final_status == ExecutionStatus.DENIED),
                sanitized_payload={"status": final_status.value, "summary": summary},
            )
        )

        completed_at = datetime.now(timezone.utc).isoformat()
        trace = ExecutionTrace(
            execution_id=execution_id,
            customer_id=parsed_request.customer_id,
            action=parsed_request.action,
            status=final_status,
            summary=summary,
            events=events,
            final_result=final_data,
            started_at=started_at,
            completed_at=completed_at,
        )

        return AgentResponse(
            execution_id=execution_id,
            status=final_status,
            summary=summary,
            data=final_data,
            trace=trace,
        )
