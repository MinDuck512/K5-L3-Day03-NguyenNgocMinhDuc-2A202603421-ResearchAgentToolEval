---
name: send
track: bonus
kind: action
provider: Telegram Bot API
requires_env: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]
inputs: [text, confirmed]
outputs: [status]
side_effect: true
requires_confirmation: true
---
# send

Posts literal text to a Telegram channel. Only the boolean `true` is accepted;
strings such as `"false"` never authorize sending. Text must contain 1–4096 characters.
The UI shows a preview and requires a button click; the CLI requires `/confirm`.
Evaluation disables sending regardless of model arguments. Telegram must acknowledge
`ok=true` before the tool reports success. API tokens are redacted from errors.
