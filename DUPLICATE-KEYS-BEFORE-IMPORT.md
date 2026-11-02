# Check duplicate keys before parsing or reformatting

When a configuration object repeats a member name, loading and saving it can erase the evidence. In Python's default parser, the last value survives:

```python
import json
raw = '{"service":{"port":8000,"port":9000}}'
parsed = json.loads(raw)
print(parsed["service"]["port"])  # 9000
```

If you check `json.dumps(parsed)` afterward, the duplicate is already gone. Check the original file before your import, formatter, or configuration loader runs.

## Run a preflight on the original file

Download [JSON Key Check](https://codeload.github.com/Dexter-Ou/json-key-check/zip/3e7572209154879b32f02934f54466f1a741fda1), extract it, and open a terminal in its directory. Requires Python 3.10 or newer. Linux Python 3.12.15 was tested; other platforms and Python versions are untested.

For the bundled duplicate example:

```sh
python3 json_key_check.py examples/duplicate.json
```

Exit status 1 means duplicate members were found. The report identifies `/service/port` with two occurrences. It reports locations and counts, not the conflicting values. Exit status 0 means no duplicate members were detected; status 2 means an input or output error. A clean result does not validate your application's configuration schema.

To gate a local import, replace `config.json` with your trusted, stopped configuration file:

```sh
python3 json_key_check.py config.json && python3 your_import.py config.json
```

The second command runs only after a clean preflight. The file must remain unchanged between the check and import. This command does not make that sequence atomic or protect against hostile file replacement.

## What the example establishes

An automated synthetic example on Linux Python 3.12.15 retained port 9000 in the default parser. Checking the original bytes returned status 1 with two occurrences at `/service/port`; checking the reserialized dictionary returned status 0. Once overwritten members have been discarded, this checker cannot reconstruct them.

## Limits and data handling

Use trusted, stopped regular UTF-8 files up to 2 MiB. Do not run it against active or hostile directories. Reports include member names in paths, which can be sensitive; keep them private when appropriate. The checker reads locally and does not upload input. Review the [README](README.md) for parser limits and usage. It does not repair files, validate schemas, or decide which repeated value is intended.

Found a setup problem or missing workflow? Describe it in the repository's Issues without posting private configurations, sensitive member names, or credentials.
