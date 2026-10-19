"""Settings and limits shared across the pipeline. Regexes and SQL stay beside their code."""

from pathlib import Path

# Paths (relative to the repo root)
CHECKOUT = Path("data/handbook")
DOCUMENTS_SCHEMA = Path("db/init/002_documents.sql")
CHUNKS_SCHEMA = Path("db/init/003_chunks.sql")
TRACE_PATH = Path("runs/ask.jsonl")

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
DEFAULT_EMBED_MODEL = "openai:text-embedding-3-small"
# Known output dimensions, checked on every response so a mismatch fails before insert.
EMBED_DIMS = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}
EMBED_BATCH = 128  # chunks per request
MAX_ATTEMPTS = 6
MAX_INPUT_TOKENS = 8192
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
EST_EMBED_USD_PER_1M = 0.02  # text-embedding-3-small
# Baseline comparison (spec 0005, AC-14): the right-page-wrong-chunk rows of run 3748df5b,
# shown per row next to every synthesis row.
COMPARE_ROWS = (52, 53, 8, 10, 99, 38, 89)
# The structural-v1 regressions vs the baseline (run 62a52a83), shown per row (spec 0006, AC-7).
REGRESSION_ROWS = (11, 34, 44, 49, 51, 58, 88, 100)
