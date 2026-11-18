# Running the app

Everything below runs inside the `app/` folder. You need Python 3.11 or later (check with `python3 --version`,
on Windows `py -0p`). The project's own environment lives in `app/.venv` and never changes your Anaconda or
system Python.

## Install (once)

macOS / Linux:

```bash
cd app
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Windows (PowerShell):

```powershell
cd app
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

If `python3` or `py` is older than 3.11 but you have Anaconda, use its Python by full path, for example
`/opt/anaconda3/bin/python -m venv .venv` (macOS) or `& "$env:USERPROFILE\anaconda3\python.exe" -m venv .venv`
(Windows).

Then open `app/.env` in an editor and put **your own** name and e-mail in `SEC_USER_AGENT` (the SEC requires
it). Never commit `.env` and never paste it into a chat. Demo mode and the tests do not need it.

## Run

```bash
.venv/bin/python -m streamlit run main.py          # Windows: .venv\Scripts\python -m streamlit run main.py
```

Then open http://localhost:8501. If the port is busy, add `--server.port 8502` and open
http://localhost:8502.

## Test

```bash
.venv/bin/python -m pytest                          # Windows: .venv\Scripts\python -m pytest
```

The tests need no `.env` and no network: outside connections are blocked during tests (`tests/conftest.py`).
The same tests run on every pull request on Linux and Windows, Python 3.11 and 3.14
(`.github/workflows/tests.yml`).

## Where things are

| Folder | What | Owner |
|---|---|---|
| `main.py`, `ui/` | Streamlit interface | D |
| `src/contracts.py` | Shared data shapes `Fact`, `CheckResult`, `CompanyData` | A |
| `src/data/` | SEC client, cache, resolver | A |
| `src/benchmarks/` | Benchmarks, industry map | B |
| `src/checks/` | The 24 checks | B (past, health), C (dividend, valuation) |
| `src/valuation/` | Valuation engine | C |
| `settings.yaml` | Thresholds and assumptions, one section per owner | each section's owner |
| `tests/` | Unit, integration, app and reconciliation tests | each owner for their code |

Full table and rules: `docs/architecture.md`.
