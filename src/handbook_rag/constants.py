"""Settings and limits shared across the pipeline. Regexes and SQL stay beside their code."""

from pathlib import Path

# Paths (relative to the repo root)
CHECKOUT = Path("data/handbook")
DOCUMENTS_SCHEMA = Path("db/init/002_documents.sql")
CHUNKS_SCHEMA = Path("db/init/003_chunks.sql")
TRACE_PATH = Path("runs/ask.jsonl")
SPEND_LOG = Path("runs/spend.jsonl")  # one line per confirmed paid run (spec 0009, AC-3)

# Permissions (spec 0007, ADR-0021)
POLICY_PATH = Path("acl/policy-v1.yaml")
IDENTITIES_PATH = Path("acl/identities-v1.yaml")
PERMISSIONS_SUITE = Path("docs/eval/permissions-v1.md")
PERMISSIONS_RUNS = Path("runs/permissions")
PERMISSIONS_KS = (5, 20)  # AC-12: k=5 frozen, plus depth 20
QUALITY_SET_USER = "admin"  # AC-9: the quality set runs as admin

# Chunking (spec 0003, AC-1)
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOKENIZER = "cl100k_base"
CHUNK_BATCH = 500  # rows per upsert
# Chunk configs coexist in one table, keyed by config_id (spec 0005, AC-1; ADR-0020). Defined
# here; the first chunk run of a config records it in chunk_configs, later runs fail on drift.
BASELINE_CONFIG = "fixed-512-64"
CHUNK_CONFIGS = {
    "fixed-512-64": {"strategy": "fixed", "params": {"size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP}},
    "structural-v1": {
        "strategy": "structural",
        "params": {"max_tokens": 512, "overlap": 64, "min_tokens": 64},
    },
    # Spec 0006, AC-1: packed sections; the prefix configs differ only in the embedded text.
    "structural-v2": {
        "strategy": "structural-packed",
        "params": {"max_tokens": 512, "overlap": 64},
    },
    "structural-v3": {
        "strategy": "structural-packed",
        "params": {"max_tokens": 512, "overlap": 64, "embed_prefix": "title-path"},
    },
    "fixed-512-64-prefixed": {
        "strategy": "fixed",
        "params": {"size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP, "embed_prefix": "title-path"},
    },
}

# Embedding (spec 0003, AC-3)
DEFAULT_EMBED_MODEL = "openai:text-embedding-3-large@1536"
# Per-model facts, keyed by `provider:model` without `@dims` (spec 0008, AC-1 to AC-5).
#   native_dims: output size without `@dims`; every response is checked against the size in use.
#   min_dims: smallest `@dims` the model accepts; None means the size can't be changed.
#   max_input_tokens: the provider's limit in the model's own tokens. Inputs are counted with
#     cl100k: exactly against it when exact_tokenizer, else against half of it (AC-4).
#   query_template: how a query-mode input is sent (AC-3); None sends the text as-is.
EMBED_MODELS = {
    "openai:text-embedding-3-small": {
        "native_dims": 1536,
        "min_dims": 1,
        "max_input_tokens": 8192,
        "exact_tokenizer": True,
        "usd_per_1m": 0.02,
        "price_source": "developers.openai.com/api/docs/pricing, 2026-10-21",
        "query_template": None,
    },
    "openai:text-embedding-3-large": {
        "native_dims": 3072,
        "min_dims": 1,
        "max_input_tokens": 8192,
        "exact_tokenizer": True,
        "usd_per_1m": 0.13,
        "price_source": "developers.openai.com/api/docs/pricing, 2026-10-21",
        "query_template": None,
    },
    "deepinfra:Qwen/Qwen3-Embedding-8B": {
        "native_dims": 4096,
        "min_dims": 32,
        "max_input_tokens": 32768,
        "exact_tokenizer": False,
        "usd_per_1m": 0.010,
        "price_source": "deepinfra.com/Qwen/Qwen3-Embedding-8B, 2026-10-21",
        # Model card format: no space after "Query:"; documents carry no instruction.
        "query_template": (
            "Instruct: Given a question about the GitLab handbook, retrieve the passages "
            "that answer it\nQuery:{q}"
        ),
    },
}
DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai"
EMBED_BATCH = 128  # chunks per request
MAX_ATTEMPTS = 6
MAX_REQUEST_TOKENS = 300_000
BACKOFF_BASE = 1.0
BACKOFF_CAP = 60.0
PROGRESS_EVERY = 10  # batches
RETRY_4XX = {408, 409}  # request timeout, conflict: transient

# Answering (spec 0003, AC-5, AC-6)
DEFAULT_ANSWER_MODEL = "openai:gpt-5.4-mini"
REASONING_EFFORT = "none"
MAX_COMPLETION_TOKENS = 1024
TOP_K = 5
MAX_CITATION = 99  # bracketed numbers above this are years or amounts, not excerpt numbers

# Eval harness (spec 0004)
EVAL_SET = Path("docs/eval/eval-set-v1.md")
EVAL_RUNS = Path("runs/eval")
EVAL_KS = (1, 3, 5, 10, 20)  # spec 0006, AC-6
EVAL_DEPTH = 20  # every answerable row is also retrieved to this depth (spec 0006, AC-6)
NDCG_K = 5
# A cited line cut by a chunk window counts if this many normalised chars sit at the chunk's
# start or end (about 8 words; spec 0004 decision, 2026-10-17). Fixed across experiments.
MIN_PIECE = 40
CORPUS_PREFIX = "content/handbook/"  # eval-set paths are relative to this; documents.path isn't
# Estimates for the cost guard (AC-8): ~3.1k in + 250 out per answer (NOTES answer-cost table).
EST_ANSWER_USD_PER_ROW = 0.004
# Baseline comparison (spec 0005, AC-14): the right-page-wrong-chunk rows of run 3748df5b,
# shown per row next to every synthesis row.
COMPARE_ROWS = (52, 53, 8, 10, 99, 38, 89)
# The structural-v1 regressions vs the baseline (run 62a52a83), shown per row (spec 0006, AC-7).
REGRESSION_ROWS = (11, 34, 44, 49, 51, 58, 88, 100)

# Retrieval modes (spec 0011). Fixed before any run, not tuned on v1.2.
RETRIEVERS = ("dense", "fts", "hybrid", "rerank")
# AC-8: hybrid is off until an ADR adopts it; spec 0012 AC-8: rerank changes it only by ADR-0023
DEFAULT_RETRIEVER = "dense"
RRF_K = 60  # AC-5: Cormack et al. 2009, fixed in their pilot
FUSION_DEPTH = 50  # AC-5: each list's depth before fusion, beyond the scored depth of 20

# Cross-encoder reranking over the dense list (spec 0012). Fixed before any run (AC-2).
# max_input_tokens: the provider's limit per query-document pair (model tokens).
# template_tokens: an estimate of the prompt template the provider wraps each pair in; used by
#   the cost estimate and the truncation guard (AC-4), which work in cl100k tokens.
# instruction: the model card's default, sent explicitly so a provider default can't drift.
RERANK_MODELS: dict[str, dict] = {
    "deepinfra:Qwen/Qwen3-Reranker-4B": {
        "endpoint": "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-4B",
        "instruction": "Given a web search query, retrieve relevant passages that answer the query",
        "max_input_tokens": 32768,
        "template_tokens": 80,
        "usd_per_1m": 0.025,
        "price_source": "deepinfra.com/Qwen/Qwen3-Reranker-4B, 2026-10-31",
    },
}
DEFAULT_RERANK_MODEL = "deepinfra:Qwen/Qwen3-Reranker-4B"
RERANK_DEPTH = 50  # AC-3: dense candidates reranked; where the 0.875 ceiling was measured
RERANK_TOKEN_MARGIN = 1.5  # AC-4: cl100k -> the reranker's tokenizer, conservatively
RERANK_TIMEOUT = 120.0  # seconds per HTTP request
# AC-11: headroom captured = (reranked@5 - floor) / (ceiling - floor), fixed before any run from
# run 2026-10-21-d83f3edc: its dense chunk_fact_recall@5 and the best top 5 from its dense top 50.
HEADROOM_FLOOR = 0.583
HEADROOM_CEILING = 0.875
# AC-11: the retrieval-side false abstentions with facts at dense ranks 6-8 (spec 0010).
RERANK_ROWS = (8, 49, 89, 53, 55)
RERANK_CURVE_KS = tuple(range(3, 11))  # AC-10: recall@k for k = 3..10, both orderings

# Recall starvation on a separate HNSW path (spec 0007 Part B, AC-17, AC-18)
ANN_RUNS = Path("runs/ann")
ANN_VECTORS = ANN_RUNS / "query-vectors.jsonl"  # query embeddings, keyed by (model, question)
ANN_MODEL = DEFAULT_EMBED_MODEL  # ADR-0022; the copy's vector(1536) type follows from it
ANN_BASELINE = EVAL_RUNS / "2026-10-21-d83f3edc"  # the AC-9 baseline the exact path must match
# pgvector 0.8.7 defaults, recorded with every run; a sweep is a follow-up.
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 64
HNSW_ITERATIVE_SCANS = ("off", "strict_order", "relaxed_order")
