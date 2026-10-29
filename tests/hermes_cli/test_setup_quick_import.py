"""First-time setup after an agent import: the default Full Setup keeps a model the import brought
unless the user chooses to reconfigure that section. (The first-run menu offers no Nous Portal
Quick Setup, so Full Setup is the default.)"""

from argparse import Namespace
from unittest.mock import patch

import pytest


def _fake_import(_hermes_home):
    """What an agent import leaves behind: a model in config.yaml and its key in .env."""
    from hermes_cli.config import load_config, save_config, save_env_value
    config = load_config()
    config["model"] = {"provider": "openrouter", "default": "anthropic/claude-sonnet-4.5"}
    save_config(config)
    save_env_value("OPENROUTER_API_KEY", "sk-or-demo-not-a-real-key")
    return "OpenClaw"


def _fake_model_step(config):
    """The real model step picks a provider and model and saves them."""
    from hermes_cli.config import save_config
    config["model"] = {"provider": "anthropic", "default": "claude-opus-4.8"}
    save_config(config)


@pytest.mark.parametrize("reconfigure, model_runs, expected_model", [
    (False, 0, {"provider": "openrouter", "default": "anthropic/claude-sonnet-4.5"}),
    (True, 1, {"provider": "anthropic", "default": "claude-opus-4.8"}),
])
def test_first_setup_keeps_imported_model_unless_user_reconfigures(reconfigure, model_runs, expected_model):
    from hermes_cli.config import get_env_value, load_config
    from hermes_cli.setup import run_setup_wizard

    questions = []

    def answer(question, choices, default=0, description=None):
        questions.append(question)
        return default  # Enter on the mode menu: Full Setup

    def yes_no(question, default=True, description=None):
        questions.append(question)
        return reconfigure if "Reconfigure model" in question else default

    with patch("hermes_cli.setup.is_interactive_stdin", return_value=True), \
            patch("hermes_cli.setup.offer_agent_import", side_effect=_fake_import), \
            patch("hermes_cli.setup.prompt_choice", side_effect=answer), \
            patch("hermes_cli.setup.prompt_yes_no", side_effect=yes_no), \
            patch("hermes_cli.setup.setup_model_provider", side_effect=_fake_model_step) as model_step, \
            patch("hermes_cli.setup.setup_terminal_backend"), \
            patch("hermes_cli.setup.setup_gateway") as gateway, \
            patch("hermes_cli.setup.setup_tools"), \
            patch("hermes_cli.setup._print_setup_summary"), \
            patch("hermes_cli.setup._record_setup_completed"):
        run_setup_wizard(Namespace(non_interactive=False, section=None, reset=False,
                                   reconfigure=False, quick=False))

    assert model_step.call_count == model_runs
    model = load_config()["model"]
    assert {k: model.get(k) for k in expected_model} == expected_model
    assert get_env_value("OPENROUTER_API_KEY") == "sk-or-demo-not-a-real-key"
    gateway.assert_called_once()  # the rest of Full Setup still runs
    assert any("Reconfigure model" in q for q in questions), questions
