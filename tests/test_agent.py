import pytest

from agentmesh.core.agent import Agent
from agentmesh.providers.mock_provider import MockProvider


def test_agent_act_uses_provider_and_records_history():
    provider = MockProvider(responses={"weather": "It is sunny."})
    agent = Agent(name="bot", provider=provider, system_prompt="You are helpful.")

    output = agent.act("What is the weather today?")

    assert output == "It is sunny."
    assert len(agent.history) == 2
    assert agent.history[0].role.value == "user"
    assert agent.history[1].role.value == "assistant"


def test_agent_act_includes_context_in_prompt():
    provider = MockProvider(default="ok")
    agent = Agent(name="bot", provider=provider)

    agent.act("Continue the analysis.", context="Prior finding: revenue grew 10%.")

    assert "Prior finding" in agent.history[0].content
    assert "Continue the analysis" in agent.history[0].content


def test_agent_use_tool_without_registry_raises():
    provider = MockProvider(default="ok")
    agent = Agent(name="bot", provider=provider)

    with pytest.raises(RuntimeError):
        agent.use_tool("calculator", expression="1+1")
