# Setting up Jina (web tools)

The example agent's built-in tools — `search_web` and `fetch_url` — use the
[Jina](https://jina.ai) API. You only need this key if your agent uses those tools.

## 1. Get an API key

1. Go to <https://jina.ai> and open the **API** section.
2. Scroll to the bottom — a **free API key** is shown right on the page. No account
   or login is required to start.

The free key comes with a starter token allowance; create an account if you need
more or want to track usage.

## 2. Save the key

Save it in both gitignored files — treat it as a secret:

- `infra/terraform.tfvars` → `jina_api_key = "jina_..."` (Terraform sets the Lambda env)
- `.env` at the repo root → `JINA_API_KEY=jina_...` (for local testing)

## Not using the web tools?

If your agent doesn't register `search_web` / `fetch_url`, you can skip this key
entirely — remove those tools from your agent's `config.py` and drop `jina_api_key`
from your variables.
