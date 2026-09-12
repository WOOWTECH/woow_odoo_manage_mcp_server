#!/usr/bin/env python3
"""Normalize a multi-document Kubernetes YAML stream for field-by-field diffing.

Drops empty documents, optionally drops Secrets, sorts the documents by
(kind, namespace, name) and re-emits them with sorted keys, so a diff only shows
real field differences and never key or document ordering.

  normalize-manifests.py [--drop-secrets] FILE...
"""
from __future__ import annotations

import sys

import yaml


def key(doc: dict) -> tuple[str, str, str]:
    meta = doc.get("metadata") or {}
    return (doc.get("kind", ""), meta.get("namespace", ""), meta.get("name", ""))


def main(argv: list[str]) -> int:
    drop_secrets = "--drop-secrets" in argv
    paths = [a for a in argv[1:] if not a.startswith("--")]
    docs: list[dict] = []
    for path in paths:
        with open(path) as fh:
            for doc in yaml.safe_load_all(fh):
                if not doc:
                    continue
                if drop_secrets and doc.get("kind") == "Secret":
                    continue
                docs.append(doc)
    docs.sort(key=key)
    for doc in docs:
        sys.stdout.write("---\n")
        yaml.safe_dump(doc, sys.stdout, sort_keys=True, default_flow_style=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
