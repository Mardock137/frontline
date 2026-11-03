import asyncio

import pytest

from agents.base_agent import BaseAgent


def test_base_agent_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseAgent(name="test")  # type: ignore[abstract]


def test_concrete_subclass_can_be_instantiated():
    class ConcreteAgent(BaseAgent):
        async def run(self, input_data):
            return {"result": input_data}

    agent = ConcreteAgent(name="TestAgent")
    assert agent.name == "TestAgent"


def test_subclass_without_run_cannot_be_instantiated():
    class IncompleteAgent(BaseAgent):
        pass

    with pytest.raises(TypeError):
        IncompleteAgent(name="Incomplete")  # type: ignore[abstract]


def test_run_is_async():
    class ConcreteAgent(BaseAgent):
        async def run(self, input_data):
            return input_data

    agent = ConcreteAgent(name="A")
    result = asyncio.run(agent.run("hello"))
    assert result == "hello"
