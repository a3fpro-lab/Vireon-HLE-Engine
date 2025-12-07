# Environment setup for Vireon HLE Engine

The engine is backend-agnostic. Choose one of:

## 1. xAI / Grok

```bash
export VIREON_BACKEND=xai
export XAI_API_KEY="sk-..."      # your xAI key
# optional:
export XAI_MODEL="grok-4"

python run_hle_eval.py

export VIREON_BACKEND=openai
export OPENAI_API_KEY="sk-..."
# optional:
export OPENAI_MODEL="gpt-5.1-thinking"

python run_hle_eval.py

export VIREON_BACKEND=dummy
python run_hle_eval.py


## Configure a backend

For full environment variable examples, see [ENVIRONMENT.md](ENVIRONMENT.md).

Choose a provider via the `VIREON_BACKEND` env var.

