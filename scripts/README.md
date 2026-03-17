# Scripts

## `run_requirements_pipeline.py`
This script is the public compatibility entrypoint for the requirements runner:

1. Ingest the requirements source.
2. Extract domain signals from the document.
3. Generate project docs and the skill tree.
4. Materialize project docs and the skill tree.

### Usage
```bash
python3 scripts/run_requirements_pipeline.py \
  --requirements docs/product-requirements.docx \
  --project-root .
```

Replace `docs/product-requirements.docx` with your own requirements file path.

### Notes
- The script supports `.docx`, `.md`, and `.txt` inputs.
- Generated `references` always stay relative to the current skill file.
- The output is designed to be rerun as the requirements evolve.

### Related commands
```bash
python3 -m skilgen.cli.main --version
python3 -m skilgen.cli.main init --project-root .
python3 -m skilgen.cli.main fingerprint --project-root .
python3 -m skilgen.cli.main intent --requirements docs/product-requirements.docx
python3 -m skilgen.cli.main features --requirements docs/product-requirements.docx --project-root .
python3 -m skilgen.cli.main plan --requirements docs/product-requirements.docx --project-root .
python3 -m skilgen.cli.main status --project-root .
python3 -m skilgen.cli.main report --project-root .
python3 -m skilgen.cli.main validate --project-root .
python3 -m skilgen.cli.main serve --host 127.0.0.1 --port 8000
```
