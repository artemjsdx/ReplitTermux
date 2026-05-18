import os, uuid, json
  from pathlib import Path

  PORT             = int(os.environ.get("RT_PORT", 9000))
  MAX_HISTORY      = int(os.environ.get("RT_MAX_HISTORY", 200))
  CMD_TIMEOUT      = int(os.environ.get("RT_CMD_TIMEOUT", 300))
  TUNNEL_KEEPALIVE = int(os.environ.get("RT_TUNNEL_KEEPALIVE", 30))

  # Token persisted across restarts so the agent always uses the same token
  _TOKEN_FILE = Path.home() / ".replittermux.token"

  def _load_or_create_token() -> str:
      env_tok = os.environ.get("RT_TOKEN", "")
      if env_tok:
          return env_tok
      if _TOKEN_FILE.exists():
          tok = _TOKEN_FILE.read_text(encoding="utf-8").strip()
          if tok.startswith("rt-"):
              return tok
      tok = "rt-" + str(uuid.uuid4())[:16]
      try:
          _TOKEN_FILE.write_text(tok, encoding="utf-8")
          _TOKEN_FILE.chmod(0o600)
      except Exception:
          pass
      return tok

  TOKEN = _load_or_create_token()
  