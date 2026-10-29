"""A provider's declared capabilities reach the agent on every gateway runtime resolution.

Launch-policy sessions (``envoy chat -q``, the dashboard chat) build their agent kwargs from
``_runtime_agent_kwargs`` alone, which used to drop ``capabilities``: a named provider's
``developer_role: false`` (or ``openai_native_compaction``) never reached those turns.
"""

from gateway.run import _runtime_agent_kwargs


def test_declared_capabilities_reach_the_agent_kwargs():
    runtime = {"provider": "custom", "base_url": "https://proxy.example/v1", "api_mode": "chat_completions",
               "capabilities": {"developer_role": False, "openai_native_compaction": True}}

    kwargs = _runtime_agent_kwargs(runtime)

    assert kwargs["capabilities"] == {"developer_role": False, "openai_native_compaction": True}


def test_non_boolean_capabilities_are_dropped():
    runtime = {"provider": "custom", "capabilities": {"developer_role": "no", "ok": True, 3: False}}

    assert _runtime_agent_kwargs(runtime)["capabilities"] == {"ok": True}
