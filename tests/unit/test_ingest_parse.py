from pathlib import Path

import pytest

from handbook_rag import corpus, ingest
from handbook_rag.ingest import derive_title, derive_url_path, skip_reason, split_front_matter


def test_refuses_when_head_differs_from_pin(monkeypatch):
    """AC-2: ingestion stops before touching the DB if HEAD != pinned SHA."""
    monkeypatch.chdir(Path(__file__).resolve().parents[2])
    monkeypatch.setattr(corpus, "git_out", lambda *args: "0" * 40 + "\n")
    with pytest.raises(SystemExit, match="!= pinned"):
        ingest.run(conn=None)


@pytest.mark.parametrize(
    ("path", "url"),
    [
        ("content/handbook/finance/expenses.md", "/handbook/finance/expenses/"),
        ("content/handbook/values/_index.md", "/handbook/values/"),
        ("content/handbook/legal/commercial/index.md", "/handbook/legal/commercial/"),
        ("content/handbook/_index.md", "/handbook/"),
        ("content/handbook/finance/ops-GPO/_index.md", "/handbook/finance/ops-gpo/"),
    ],
)
def test_url_path(path, url):
    assert derive_url_path(path) == url


@pytest.mark.parametrize(
    ("front_matter", "body", "path", "title"),
    [
        ('title: "On-Call"', "", "content/handbook/x.md", "On-Call"),
        ("Title: About\nweight: -10", "", "content/handbook/company/_index.md", "About"),
        ("title: 'Quoted'", "# H1", "content/handbook/x.md", "Quoted"),
        ("weight: 1", "intro\n# First H1\n# Second", "content/handbook/x.md", "First H1"),
        ("", "no heading", "content/handbook/legal/dmca.md", "dmca"),
        ("", "", "content/handbook/company/_index.md", "company"),
    ],
)
def test_title_fallbacks(front_matter, body, path, title):
    assert derive_title(front_matter, body, path) == title


def test_split_front_matter():
    assert split_front_matter("---\ntitle: A\n---\n\nBody\n") == ("title: A", "\nBody\n")
    assert split_front_matter("No front matter") == ("", "No front matter")


@pytest.mark.parametrize(
    ("front_matter", "body", "reason"),
    [
        ("draft: true", "content", "draft"),
        ("draft: true", "", "draft"),
        ("draft: false", "content", None),
        ("title: X", "  \n", "empty_body"),
        ('title: X\nredirect_to: "/handbook/y/"', "This page has moved", None),
    ],
)
def test_skip_reason(front_matter, body, reason):
    assert skip_reason(front_matter, body) == reason


@pytest.mark.parametrize(
    ("url", "url_path"),
    [
        ("/handbook/upstream-studios/", "/handbook/upstream-studios/"),
        ('"https://handbook.gitlab.com/handbook/engineering/Prep/"', "/handbook/engineering/prep/"),
        ("/handbook/engineering/on-call", "/handbook/engineering/on-call/"),
        ("'/handbook/a/#section'", "/handbook/a/"),
    ],
)
def test_normalize_url_path(url, url_path):
    """Spec 0007, AC-3: a redirect target is normalized like a stored url_path: an absolute
    handbook.gitlab.com URL reduced to its path, lowercased, with a trailing slash."""
    assert ingest.normalize_url_path(url) == url_path


def test_normalize_rejects_other_host():
    """Spec 0007, AC-3: a target on another host can't be in the corpus."""
    with pytest.raises(ValueError, match="handbook.gitlab.com"):
        ingest.normalize_url_path("https://about.gitlab.com/handbook/x/")


def test_derive_redirect():
    """Spec 0007, AC-3: `redirect_to:` is read from the front matter; a normal page has none."""
    assert ingest.derive_redirect('title: X\nredirect_to: "/handbook/Y/"') == "/handbook/y/"
    assert ingest.derive_redirect("title: X") is None


def test_url_path_keeps_file_name_characters():
    """Spec 0007, AC-3 review fix: a file path is not a URL, so `#` and `?` in a file name stay
    in its url_path (as before the redirect change)."""
    assert derive_url_path("content/handbook/c#-guide.md") == "/handbook/c#-guide/"
