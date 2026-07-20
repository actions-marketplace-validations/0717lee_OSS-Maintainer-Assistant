"""Shared pytest fixtures: the offline demo corpus, config, and agent context."""
import pytest

from maintainer_agent.core.config import config_for_repo
from maintainer_agent.github import GitHubClient
from maintainer_agent.orchestrator.state import build_context


@pytest.fixture
def items():
    return GitHubClient(offline=True).list_items()


@pytest.fixture
def config():
    return config_for_repo("octocat/octo-demo")


@pytest.fixture
def by_number(items):
    return {it.number: it for it in items}


@pytest.fixture
def ctx(items, config):
    return build_context(items, config)
