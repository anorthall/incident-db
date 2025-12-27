from __future__ import annotations

from .base import DataOperation, OperationResult, OperationResultStatus, load_prompt

_REGISTRY: dict[str, type[DataOperation]] = {}


def register_operation(cls: type[DataOperation]) -> type[DataOperation]:
    _REGISTRY[cls.name] = cls
    return cls


from . import (  # noqa: E402, F401
    clean_analysis_comments,
    clean_references,
    detect_incomplete_text,
    fix_hyphenated_words,
    generate_summaries,
    generate_titles,
    infer_dates,
    normalize_whitespace,
    remove_duplicate_sources,
    suggest_tags,
)


def get_operation(name: str) -> DataOperation:
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(f"Unknown operation: {name}. Available: {available}")
    return _REGISTRY[name]()


def get_all_operations() -> list[DataOperation]:
    ops = [cls() for cls in _REGISTRY.values()]
    return sorted(ops, key=lambda op: (op.requires_llm, op.name))


def list_operations() -> list[str]:
    return sorted(_REGISTRY.keys())


__all__ = [
    "DataOperation",
    "OperationResult",
    "OperationResultStatus",
    "get_all_operations",
    "get_operation",
    "list_operations",
    "load_prompt",
    "register_operation",
]
