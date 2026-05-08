"""
tunnel.py — Tunnel management: Cloudflare (primary) → localhost.run (fallback).
S:  One responsibility — establish public tunnel and report URL.
O:  New providers can be added by subclassing TunnelProvider.
L:  All TunnelProvider subclasses are substitutable.
D:  BridgeTunnel depends on TunnelProvider abstraction.
"""
from __future__ import annotations
import re, subprocess, threading
from abc import ABC, abstractmethod
from typing import Callable


UrlCallback = Callable[[str], None]


class TunnelProvider(ABC):
    """Abstract tunnel provider — open for extension, closed for modification."""

    @abstractmethod
    def start(self, port: int, on_url: UrlCallback) -> None: ...


class CloudflareTunnel(TunnelProvider):
    """
    Uses `cloudflared tunnel --url` (Quick Tunnel — no account needed).
    Install on Termux: pkg install cloudflared
    """
    def start(self, port: int, on_url: UrlCallback) -> None:
        cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        _URL_RE = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
        for line in proc.stdout:  # type: ignore[union-attr]
            m = _URL_RE.search(line)
            if m:
                on_url(m.group(0))
                return


class LocalhostRunTunnel(TunnelProvider):
    def start(self, port: int, on_url: UrlCallback) -> None:
        cmd = [
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-R", f"80:localhost:{port}", "nokey@localhost.run",
        ]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in proc.stdout:  # type: ignore[union-attr]
            line = line.strip()
            if ".lhr.life" in line or ".localhost.run" in line:
                for part in line.split():
                    if part.startswith("http"):
                        on_url(part.strip(".,"))
                        return


class BridgeTunnel:
    """
    Tries providers in order; falls back to localhost URL if all fail.
    D: injected providers, not hard-coded.
    """

    def __init__(
        self,
        port: int,
        on_url: UrlCallback,
        providers: list[TunnelProvider] | None = None,
    ) -> None:
        self._port      = port
        self._on_url    = on_url
        self._providers = providers or [CloudflareTunnel(), LocalhostRunTunnel()]

    def start_async(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        for provider in self._providers:
            try:
                provider.start(self._port, self._on_url)
                return
            except FileNotFoundError:
                continue
            except Exception:
                continue
        # All providers failed — use local URL
        self._on_url(f"http://localhost:{self._port}")
