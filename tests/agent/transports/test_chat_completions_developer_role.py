"""The ``developer`` role swap for GPT-5 models honours a provider's ``developer_role`` capability.

The Tanzu AI Service proxy serves gpt-5.x but answers HTTP 500 to a ``developer`` message, so its
provider entry declares ``capabilities: {developer_role: false}``.
"""

import pytest

from agent.transports import get_transport


@pytest.fixture
def transport():
    import agent.transports.chat_completions  # registers the transport
    return get_transport("chat_completions")


MESSAGES = [{"role": "system", "content": "You are Envoy."}, {"role": "user", "content": "hi"}]


def _first_role(transport, **params):
    kwargs = transport.build_kwargs(model="gpt-5.4", messages=list(MESSAGES), tools=None,
                                    base_url="https://genai-proxy.example/v1", **params)
    return kwargs["messages"][0]["role"]


def test_gpt5_system_prompt_goes_out_as_developer_by_default(transport):
    assert _first_role(transport) == "developer"


def test_provider_without_developer_role_keeps_system(transport):
    assert _first_role(transport, developer_role=False) == "system"
