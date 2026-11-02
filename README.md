# JSON Key Check

Find duplicate object member names before a JSON import silently keeps only one
value. Runs locally with Python 3.10+ and its standard library; no installation,
network connection or dependencies. This is an early command-line preview.

[Download the source ZIP](https://codeload.github.com/Dexter-Ou/json-key-check/zip/3e7572209154879b32f02934f54466f1a741fda1),
extract it, and open a terminal in the extracted `json-key-check-3e7572209154879b32f02934f54466f1a741fda1`
folder containing `json_key_check.py`. The download is pinned to this preview.

Save your JSON file, then run from this extracted folder:

```sh
python3 json_key_check.py examples/duplicate.json
```

The example reports `/service/port` occurring twice and exits **1**. Run
`python3 json_key_check.py examples/clean.json` for a clean result and exit **0**.
Malformed input, invalid UTF-8, non-finite literals, input over 2 MiB, excessive
nesting and file errors produce exit **2**. Reports go to standard output as JSON.
No input is rewritten. Use trusted, stopped regular files; there is no atomic
snapshot or protection against an adversary changing parent directories.

The checker compares decoded names: `"a"` and `"\u0061"` collide. It examines
objects inside arrays and inside every repeated member, including values a normal
dictionary parser would discard. Names are case sensitive and are not Unicode
normalized. Scalars and arrays at the root are valid. A UTF-8 BOM is accepted.
Large numeric spellings are checked as JSON syntax without floating-point rounding.

Reports omit values and file paths, but **member names appear in JSON pointers**;
treat reports as potentially sensitive. `/` and `~` in names are escaped as `~1`
and `~0`. Pointers beneath repeated parent names can refer to multiple occurrences;
they are navigation hints, not unique source locations. At most 100 duplicate
groups are listed, with a full group count and a truncation flag. Maximum container
depth is 64 below the root. JSON schema, business rules and authenticity are not
validated. A clean result does not establish that a file is safe to execute/import.

To run the synthetic checks: `python3 -m unittest -v test_json_key_check.py`.
Tested on Linux with Python 3.12.15 using eight synthetic test methods.
Python 3.10/3.11, Windows and macOS remain untested; check them before reliance.

Free MIT-licensed preview from Gong LLC. For feedback, describe setup problems,
unclear reports or missing capabilities; do not post private JSON or reports
containing sensitive member names.
