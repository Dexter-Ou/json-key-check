#!/usr/bin/env python3
"""Read-only duplicate JSON member checker. Python 3.10+, standard library."""
import argparse
import json
import os
import stat
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 64
MAX_FINDINGS = 100


class ObjectPairs(list):
    """Distinguish JSON objects from arrays without collapsing members."""


class InvalidInput(ValueError):
    pass


def reject_constant(_value):
    raise InvalidInput("non_finite_number")


def inspect_bytes(raw):
    if len(raw) > MAX_BYTES:
        raise InvalidInput("size_limit")
    try:
        tree = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=ObjectPairs,
                          parse_constant=reject_constant, parse_int=str, parse_float=str)
    except UnicodeError:
        raise InvalidInput("invalid_utf8") from None
    except json.JSONDecodeError:
        raise InvalidInput("invalid_json") from None
    except RecursionError:
        raise InvalidInput("depth_limit") from None
    findings = []
    total = 0
    stack = [(tree, "", 0)]
    while stack:
        node, path, depth = stack.pop()
        if isinstance(node, (ObjectPairs, list)):
            if depth > MAX_DEPTH:
                raise InvalidInput("depth_limit")
            if isinstance(node, ObjectPairs):
                counts = {}
                for key, _ in node:
                    counts[key] = counts.get(key, 0) + 1
                for key, count in counts.items():
                    if count > 1:
                        total += 1
                        if len(findings) < MAX_FINDINGS:
                            findings.append({"pointer": path + "/" + escape(key),
                                             "occurrences": count})
                children = [(value, path + "/" + escape(key), depth + 1)
                            for key, value in node]
            else:
                children = [(value, path + "/" + str(i), depth + 1)
                            for i, value in enumerate(node)]
            stack.extend(reversed(children))
    return {"status": "duplicates" if total else "clean",
            "duplicate_groups": total, "findings": findings,
            "findings_truncated": total > len(findings)}


def escape(key):
    return key.replace("~", "~0").replace("/", "~1")


def read_input(path):
    # No writes. Refuse nonregular files and final symlinks on supported systems.
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise InvalidInput("not_regular_file")
        return stream.read(MAX_BYTES + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="trusted, stopped UTF-8 JSON file (maximum 2 MiB)")
    args = parser.parse_args()
    try:
        report = inspect_bytes(read_input(args.file))
        code = 1 if report["duplicate_groups"] else 0
    except InvalidInput as exc:
        report, code = {"status": "error", "error": str(exc)}, 2
    except OSError:
        report, code = {"status": "error", "error": "input_io"}, 2
    try:
        print(json.dumps(report, ensure_ascii=True, allow_nan=False))
        sys.stdout.flush()
    except (OSError, UnicodeError):
        return 2
    return code


if __name__ == "__main__":
    sys.exit(main())
