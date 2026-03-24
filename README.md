# AI Incident Investigation System

Day 1 foundation includes a minimal FastAPI app and health endpoint.

## Environment Configuration

The app now loads settings from `.env` through `app/core/config.py`.

Key values:

- `APP_NAME`
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Verify health endpoint:

   ```bash
   curl http://127.0.0.1:8000/health
   ```

## Simple Commands (Production-Style)

Use the `Makefile` targets:

```bash
make install
make dev
make run
make test
make lint
```
