import pytest

from agentmesh.tools.builtin import CalculatorTool, WordCountTool
from agentmesh.tools.registry import ToolRegistry


def test_calculator_tool_basic():
    calc = CalculatorTool()
    assert calc.run(expression="2 + 3 * 4") == "14"


def test_calculator_tool_invalid_expression_returns_error_string():
    calc = CalculatorTool()
    result = calc.run(expression="import os")
    assert result.startswith("error:")


def test_word_count_tool():
    wc = WordCountTool()
    assert wc.run(text="the quick brown fox") == "4"


def test_registry_register_and_invoke():
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    assert "calculator" in registry
    assert registry.invoke("calculator", expression="10 / 2") == "5.0"


def test_registry_duplicate_registration_raises():
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    with pytest.raises(ValueError):
        registry.register(CalculatorTool())


def test_registry_unknown_tool_raises():
    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.get("nope")
