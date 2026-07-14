from app.models.events import AIActivityEvent, AgentName, AIActivityStatus
from app.services.business_intelligence import BusinessIntelligence


def test_business_intelligence_preserves_openai_request_telemetry() -> None:
    intelligence = BusinessIntelligence(
        ai_status="completed",
        ai_model="gpt-test",
        ai_request_id="req_123",
        ai_input_tokens=120,
        ai_output_tokens=45,
    )

    payload = intelligence.as_event_payload()

    assert payload["ai_request_id"] == "req_123"
    assert payload["ai_input_tokens"] == 120
    assert payload["ai_output_tokens"] == 45


def test_ai_activity_identifies_its_owning_agent() -> None:
    event = AIActivityEvent(
        agent=AgentName.BUSINESS,
        status=AIActivityStatus.COMPLETED,
        capability="business_intelligence",
    )

    assert event.agent == AgentName.ORACLE
