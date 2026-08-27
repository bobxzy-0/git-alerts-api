from unittest.mock import Mock

import pytest

from core.sources import RepositoryTarget, get_source_adapter
from core.sources.github import GitHubAdapter
from core.sources.gitlab import GitLabAdapter
from core.sources.gitee import GiteeAdapter
from scans.models import Scan


def repository(name="repo", owner_type="Organization"):
    return {
        "html_url": f"https://github.com/example/{name}",
        "full_name": f"example/{name}",
        "owner": {"type": owner_type},
    }


def test_github_adapter_returns_unified_repository_targets():
    adapter = GitHubAdapter("token")
    adapter.client = Mock()
    adapter.client.search_code.return_value = [
        {"repository": repository()},
        {"repository": repository()},
    ]

    targets = adapter.search(Scan.ScanTypes.SEARCH_CODE, "company-secret")

    assert targets == [
        RepositoryTarget(
            source="github",
            url="https://github.com/example/repo",
            owner="example",
            name="repo",
            metadata={"owner_type": "Organization"},
        )
    ]


def test_github_adapter_filters_non_organization_repositories():
    adapter = GitHubAdapter("token")
    adapter.client = Mock()
    adapter.client.search_repositories.return_value = [
        repository("org", "Organization"),
        repository("personal", "User"),
    ]

    targets = adapter.search(
        Scan.ScanTypes.SEARCH_REPOS, "example", org_repos_only=True
    )

    assert [target.name for target in targets] == ["org"]


def test_github_adapter_resolves_repository_url():
    adapter = GitHubAdapter("token")
    adapter.client = Mock()
    adapter.client.get_repository.return_value = repository()

    target = adapter.resolve("https://github.com/example/repo.git/tree/main")

    assert target is not None
    assert target.owner == "example"
    assert target.name == "repo"
    adapter.client.get_repository.assert_called_once_with("example", "repo")


def test_gitlab_adapter_returns_unified_repository_targets():
    adapter = GitLabAdapter("token")
    adapter.client = Mock()
    adapter.client.get_group_projects.return_value = [
        {
            "web_url": "https://gitlab.com/acme/platform/api",
            "path_with_namespace": "acme/platform/api",
            "visibility": "public",
            "default_branch": "main",
        }
    ]

    targets = adapter.search(Scan.ScanTypes.ORG_REPOS, "acme")

    assert targets == [
        RepositoryTarget(
            source="gitlab",
            url="https://gitlab.com/acme/platform/api",
            owner="acme/platform",
            name="api",
            metadata={"visibility": "public", "default_branch": "main"},
        )
    ]


def test_gitlab_adapter_resolves_nested_namespace_url():
    adapter = GitLabAdapter("token")
    adapter.client = Mock()
    adapter.client.get_project.return_value = {
        "web_url": "https://gitlab.com/acme/platform/api",
        "path_with_namespace": "acme/platform/api",
    }

    target = adapter.resolve("https://gitlab.com/acme/platform/api/-/tree/main")

    assert target.owner == "acme/platform"
    assert target.name == "api"
    adapter.client.get_project.assert_called_once_with("acme/platform", "api")


def test_registry_enables_gitlab_and_gitee_and_rejects_unknown_source():
    assert isinstance(get_source_adapter("gitlab", token="token"), GitLabAdapter)
    assert isinstance(get_source_adapter("gitee", token="token"), GiteeAdapter)
    with pytest.raises(ValueError, match="not enabled"):
        get_source_adapter("bitbucket", token="token")


def test_gitee_adapter_returns_unified_repository_target():
    adapter = GiteeAdapter("token")
    adapter.client = Mock()
    adapter.client.search_repositories.return_value = [{
        "html_url": "https://gitee.com/acme/api", "full_name": "acme/api",
        "private": False, "default_branch": "master",
    }]
    target = adapter.search(Scan.ScanTypes.SEARCH_REPOS, "acme")[0]
    assert target.source == "gitee"
    assert target.owner == "acme"
    assert target.name == "api"
