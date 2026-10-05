# Environment: services a session relies on

The game environment (Wine, Xvfb, the executables, `IC2_WORK`) is in `CLAUDE.md` "Environment" and `docs/wsl-setup.md`. This file is
for the services around it. Adopted 2026-10-05 from harness_imperial (L50/L51; the rules themselves are in `CLAUDE.md`, Code map).

## Model quota availability: quota-tracker

A local service, quota-tracker, reports how much subscription quota is left on these providers: claude, openai (ChatGPT plan, used
via OpenCode), zai (GLM Coding Plan), opencode_go (OpenCode Go), openrouter (prepaid credit) and alibaba (Alibaba Token Plan). Check it whenever you need to know
whether a provider can be used right now, before choosing, recommending or delegating to a model.

### Querying (read-only, localhost, no auth, results cached 60 s)
- `curl -s localhost:8765/quota`: every provider
- `curl -s localhost:8765/quota/<provider>`: one provider
- `curl -s localhost:8765/best`: providers with quota left, most headroom first
- `curl -s localhost:8765/avoid`: providers out of quota, with when each is usable again
- Add `?refresh` to bypass the cache.

Each provider has:
- `status`: `ok` (under 80% used), `low` (80% or more), `exhausted` (95% or more: don't use until `available_at` /
  `available_in`), `error` (couldn't be checked; `error` says why), `not_configured`
- `headroom_pct`: percent left on its most-used window
- `windows[]`: every limit, with `name`, `used_pct`, `resets_at` (unix s), `resets_in`

### Usage history
- `curl -s 'localhost:8765/usage?since=7d'`: per provider, the models called, with `calls`, `sessions`, `tokens` and `effort`
  (reasoning effort per call: Claude Code `effort`, OpenCode `variant`, Codex `effort`; `default` = none set).
- `curl -s 'localhost:8765/usage/sessions?since=7d&model=glm-5.3&effort=high'`: the sessions behind those calls, with `title`,
  `project`, `tool`, `data_dir` (which OpenCode database) and `launched_by` (the Claude Code session that started it, when it ran
  in a Claude scratchpad). Filters: `provider`, `model`, `effort`, all optional.
- `since` accepts `90m`, `24h`, `7d`, `4w` or `all`. For zai, totals come from Z.ai's own API and include other machines.
- The tracker reports availability and history only; choosing a model is up to the session and the owner.

### Models per provider
| provider    | heavy                                             | light                                                 |
|-------------|---------------------------------------------------|-------------------------------------------------------|
| claude      | `claude --model opus`                             | `claude --model sonnet`                               |
| openai      | `opencode -m openai/gpt-6.1-sol`                  | `opencode -m openai/gpt-5.6-luna`                     |
| zai         | `opencode -m zai-coding-plan/glm-5.3`             | `opencode -m zai-coding-plan/glm-5.3-flash`           |
| opencode_go | `opencode -m opencode-go/deepseek-v4-pro`         | `opencode -m opencode-go/deepseek-v4.1-flash`         |
| openrouter  | `opencode -m openrouter/deepseek/deepseek-v4-pro` | `opencode -m openrouter/deepseek/deepseek-v4.1-flash` |
| alibaba: DeepSeek | `opencode -m alibaba-token-plan/deepseek-v4-pro` | `opencode -m alibaba-token-plan/deepseek-v4.1-flash` |
| alibaba: Qwen     | `opencode -m alibaba-token-plan/qwen3.8-max`     | `opencode -m alibaba-token-plan/qwen3.8-flash`       |
| alibaba: GLM      | `opencode -m alibaba-token-plan/glm-5.3`         | none on alibaba (zai has `glm-5.3-flash`)            |

With `scripts/external_review.py` a model is passed as `--model <id>#<effort>`. Use effort `low` or `medium` for a heavy model and
`high` for a light one (`CLAUDE.md`, "Effort").

Facts that affect availability:
- `gpt-5.6-luna` has its own weekly limit: for light tasks openai is usable while the `gpt-5.6-luna:7d` window in `/quota/openai`
  is under 95%, even if openai is exhausted.
- openrouter is prepaid credit: its windows never reset, and `remaining_usd` is the balance.
- alibaba has one monthly credit pool shared by every model on the plan (DeepSeek, Qwen, GLM). Its window is named `month`
  (no 5-hour or weekly windows); the response also has `plan` and `subscription_ends_at`. If quota-tracker shows
  `not_configured` or a login error, ask the owner to run `bl auth login --console --console-site international`.
- **alibaba in OpenCode** (usable since 2026-10-05): the key comes from the environment variable `ALIBABA_TOKEN_PLAN_API_KEY`
  (on WSL it comes from `~/.config/ai-keys.env`, loaded by `~/.bashrc` and `~/.profile`, and for commands started from Windows from `WSLENV`; on Windows it is a user variable; that file holds keys and is never read or printed), so it works in every OpenCode data folder, the reviewer's `$IC2_WORK/opencode-data` included.
  - Never add it to an `auth.json` with `opencode auth login`: a key stored there overrides the variable, and a bad one breaks
    the provider for that folder. Never print, copy or edit the key or any `auth.json`.
  - A session started before the variable existed doesn't have it: start OpenCode (and `scripts/external_review.py`) through
    `bash -ic '…'`, or open a new shell.
  - The owner's plan is Personal edition: the Kimi and MiniMax models OpenCode lists are Team-only and fail.
  - Night discount, 22:00-08:00 UTC+8: DeepSeek uses 50% fewer credits, Qwen 60% fewer.
  - Quick check: `opencode run -m alibaba-token-plan/qwen3.8-flash "Reply with just: ok"`.
  - **"Invalid API-key":** a stale Alibaba entry in that folder's `auth.json` overrides the variable. Tell the owner which
    `XDG_DATA_HOME` was used.
  - **"Provider not found":** the variable is missing from the environment. Restart the session or shell so it picks it up
    (or run through `bash -ic`). A harness that cleans the environment won't see it either. If it is still missing, tell the
    owner rather than retrying.

### If the service isn't running
Check: `curl -sf localhost:8765/health`. If that fails:
1. `systemctl --user restart quota-tracker`, wait a few seconds, check `/health` again.
2. If systemctl says `Failed to connect to bus`, the user's systemd instance isn't running: ask the owner to run
   `sudo loginctl enable-linger $USER`, then retry step 1.
3. If it still fails, read `journalctl --user -u quota-tracker -n 50` and tell the owner what it says.
4. To run it without the service: `cd ~/projects/models_quota_tracker && uv run quota-tracker serve` (in the background; it stops
   when the session ends).

### Don't
- Don't read or edit `~/.config/quota-tracker/config.toml`; it holds account tokens.
- If a provider shows `error` about an expired cookie or token, tell the owner; renewing it needs their browser or login.
