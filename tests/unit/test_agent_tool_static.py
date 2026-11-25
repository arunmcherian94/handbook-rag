"""Static check that chunks reach the agent only through ask.search (spec 0013, AC-3)."""

import ast
import inspect
import re
import uuid
from pathlib import Path

from fakes import FakeChatModel, final_step, make_principal, tool_step

from handbook_rag import ask
from handbook_rag.agent.loop import run_turn
from handbook_rag.agent.tool import TOOL, TurnTool
from handbook_rag.ask import Retrieved

SRC = Path(__file__).resolve().parents[2] / "src" / "handbook_rag"
# Reading the chunks table is what AC-3 forbids. chunk_embeddings may appear only in the dry
# run's "any vectors for this model?" check, copied from ask.main: it returns no chunk.
READS_CHUNKS = re.compile(r"\b(FROM|JOIN)\s+chunks\b", re.IGNORECASE)
EMBEDDINGS = re.compile(r"chunk_embeddings", re.IGNORECASE)
PRESENCE_CHECK = "SELECT EXISTS (SELECT 1 FROM chunk_embeddings WHERE model = %s)"


def test_no_chunk_reading_sql_in_agent_modules():
    """AC-3: no string constant in agent/ or models/chat/ reads the chunks table; the only
    chunk_embeddings statement is the embedding-model presence check."""
    files = [*(SRC / "agent").rglob("*.py"), *(SRC / "models" / "chat").rglob("*.py")]
    assert len(files) >= 4
    hits = []
    for f in files:
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
                if READS_CHUNKS.search(text) or (
                    EMBEDDINGS.search(text) and text.strip() != PRESENCE_CHECK
                ):
                    hits.append(f"{f.name}:{node.lineno}")
    assert hits == []


def test_default_retriever_is_ask_retrieve():
    """AC-3: the tool's default retriever is ask.retrieve itself."""
    default = inspect.signature(TurnTool.__init__).parameters["retrieve"].default
    assert default is ask.retrieve


NETWORK_MODULES = (
    "requests",
    "httpx",
    "urllib.request",
    "http.client",
    "socket",
    "aiohttp",
    "smtplib",
    "subprocess",
)


def _imported(tree: ast.AST) -> set[str]:
    """Every module name an import statement could bring in, including `from urllib import
    request` as urllib.request."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
            names |= {f"{node.module}.{a.name}" for a in node.names}
    return names


def test_tools_list_is_exactly_the_retrieve_tool():
    """0014 AC-13: every ChatModel.complete call gets tools == [TOOL], and TOOL is `retrieve`."""
    assert TOOL["function"]["name"] == "retrieve"
    found = [
        Retrieved(
            n=i,
            chunk_id=uuid.uuid4(),
            doc_id=uuid.uuid4(),
            url_path=f"/handbook/x/{i}/",
            heading=f"H{i}",
            content=f"content {i}",
            distance=0.1,
            chunk_size=512,
            chunk_overlap=64,
            tokenizer="cl100k_base",
            commit_sha="abc",
        )
        for i in range(1, 6)
    ]
    tool = TurnTool(None, None, make_principal("staff"), retrieve=lambda *a, **kw: found)
    model = FakeChatModel([tool_step("q"), final_step("no cite"), final_step("Fact [1].")])
    rec = run_turn(model, tool, "Q?", [], lambda r: None)
    assert rec["state"] == "answered" and len(model.calls) == 3
    assert all(call["tools"] == [TOOL] for call in model.calls)


def test_agent_modules_import_no_network_client():
    """0014 AC-13: no module in handbook_rag.agent (guardrails.py included) imports a network
    client, process spawner or mail library."""
    files = sorted((SRC / "agent").rglob("*.py"))
    assert "guardrails.py" in {f.name for f in files}
    hits = []
    for f in files:
        for name in _imported(ast.parse(f.read_text())):
            if any(name == m or name.startswith(m + ".") for m in NETWORK_MODULES):
                hits.append(f"{f.name}: {name}")
    assert hits == []


def test_import_scanner_sees_every_import_form():
    """0014 AC-13: the scanner catches `import urllib.request` and `from urllib import request`."""
    tree = ast.parse("import urllib.request\nfrom urllib import request\nfrom socket import x")
    names = _imported(tree)
    assert {"urllib.request", "socket"} <= names
