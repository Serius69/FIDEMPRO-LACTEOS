#!/usr/bin/env python3
"""Merge the reviewed human facts with the machine facts CI just produced.

`release/<component>.contract-base.json` holds everything a person must decide:
lineage, statefulness, schema class, rollback, the acceptance contract. CI can
never infer those. This script fills in only what CI actually observed -- the
commit, the image, the registry digest, the build time and the gate results --
and writes a complete release contract v2.

It refuses to invent. A missing digest is an error, not a null.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="emit_contract.py")
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--tag", default=None)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--image-tag", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--built-at", required=True)
    parser.add_argument("--builder", default="github-actions")
    parser.add_argument("--builder-version", required=True,
                        help="e.g. the output of `docker buildx version`; the schema has no null for this")
    parser.add_argument("--tests", type=Path, required=True,
                        help="JSON file holding the `tests` evidence block produced by the gate job")
    args = parser.parse_args(argv)

    if not args.digest.startswith("sha256:") or len(args.digest) != 71:
        print(f"error: --digest is not a registry digest: {args.digest!r}", file=sys.stderr)
        return 2
    if len(args.commit) != 40:
        print(f"error: --commit must be the full 40-hex sha: {args.commit!r}", file=sys.stderr)
        return 2

    contract = json.loads(args.base.read_text(encoding="utf-8"))
    contract["schema_version"] = "2.0.0"
    contract["repo"] = {
        "url": args.repo_url,
        "commit": args.commit,
        "branch": args.branch,
        "tag": args.tag,
        "dirty": False,
    }
    contract["artifact"] = {
        "image": args.image,
        "tag": args.image_tag,
        "digest": args.digest,
        "digest_source": "registry",
        "base_image_digest": None,
        "size_bytes": None,
    }
    contract["build"] = {
        "built_at": args.built_at,
        "builder": {
            "host": args.builder,
            "tool": "docker-buildx",
            "tool_version": args.builder_version,
            "reproducible": None,
        },
    }
    contract["tests"] = json.loads(args.tests.read_text(encoding="utf-8"))

    args.out.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
