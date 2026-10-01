"""Credenciais locais na fronteira de transporte, fora dos snapshots."""
from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from uuid import uuid4
from urllib.parse import quote, urlsplit

from norvald_lab.vendor.norvald_execution.contracts.provider_kinds import SUPPORTED_KINDS

KINDS = ["openrouter", "openai", "anthropic", "gemini", "ollama", *[k for k in SUPPORTED_KINDS if k not in {"openrouter", "openai", "anthropic", "gemini", "ollama"}], "openai-compatible"]


def credential_env(kind):
    return "NORVALD_LAB_" + kind.upper().replace("-", "_") + "_KEY"


def validate_address(value: str):
    if not isinstance(value, str) or len(value) > 2000:
        raise ValueError("Endereço inválido.")
    if value:
        u = urlsplit(value)
        if u.scheme not in {"http", "https"} or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError("Use um endereço HTTP(S), sem chave, usuário, query ou fragmento.")
    return value.rstrip("/")


class LocalSettings:
    def __init__(self, root: Path):
        self.directory = root / "private"
        self.path = self.directory / "settings.json"
        self.lock = threading.RLock()

    def read(self):
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"live_enabled": False, "connections": {}}

    def write(self, data):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.directory.chmod(0o700)
        temp = self.path.with_suffix("." + uuid4().hex + ".tmp")
        try:
            descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            os.replace(temp, self.path)
            self.path.chmod(0o600)
        finally:
            temp.unlink(missing_ok=True)

    def connection(self, kind):
        if kind not in KINDS:
            raise ValueError("Provedor não suportado.")
        return self.read()["connections"].get(kind, {})

    def resolve(self, kind, env="", base_url=None):
        if env and os.environ.get(env):
            return os.environ[env]
        if kind not in KINDS:
            return ""
        connection = self.connection(kind)
        # A chave salva só é entregue ao endereço cadastrado para ela.
        if (base_url or "").rstrip("/") != connection.get("base_url", "").rstrip("/"):
            return ""
        return connection.get("api_key", "")

    def public(self, *, live_enabled=None):
        data = self.read()
        connections = []
        for kind in KINDS:
            c = data["connections"].get(kind, {})
            env = credential_env(kind)
            has_env = bool(os.environ.get(env))
            connections.append({"kind": kind, "credential_env": env, "base_url": c.get("base_url", ""),
                                "has_key": bool(c.get("api_key")) or has_env, "saved_key": bool(c.get("api_key")),
                                "credential_source": "environment" if has_env else "local" if c.get("api_key") else "none"})
        return {"live_enabled": data["live_enabled"] if live_enabled is None else live_enabled, "connections": connections}

    def save_connection(self, kind, payload):
        with self.lock:
            self.connection(kind)
            if set(payload) - {"api_key", "base_url"}:
                raise ValueError("Conexão aceita chave e endereço.")
            data = self.read()
            c = dict(data["connections"].get(kind, {}))
            if "base_url" in payload:
                c["base_url"] = validate_address(payload["base_url"])
            if "api_key" in payload:
                key = payload["api_key"]
                if not isinstance(key, str) or not 1 <= len(key.strip()) <= 8192 or any(ord(ch) < 32 for ch in key):
                    raise ValueError("Informe uma chave válida, sem quebras de linha.")
                c["api_key"] = key.strip()
            if kind == "openai-compatible" and not c.get("base_url"):
                raise ValueError("Informe o endereço da API compatível.")
            if kind in {"anthropic", "gemini"} and c.get("base_url"):
                raise ValueError("Este adapter usa o endereço nativo do provedor.")
            data["connections"][kind] = c
            self.write(data)
        return self.public()

    def delete_key(self, kind):
        with self.lock:
            self.connection(kind)
            data = self.read()
            data["connections"].setdefault(kind, {}).pop("api_key", None)
            self.write(data)
        return self.public()

    def set_execution(self, value):
        if type(value) is not bool:
            raise ValueError("live_enabled deve ser booleano.")
        with self.lock:
            data = self.read(); data["live_enabled"] = value; self.write(data)

    def redact(self, value, extra_keys=()):
        keys = [c.get("api_key", "") for c in self.read()["connections"].values()]
        keys += list(extra_keys)
        def clean(item):
            if isinstance(item, str):
                for key in keys:
                    if key:
                        item = item.replace(key, "[API_KEY_REDACTED]").replace(quote(key, safe=""), "[API_KEY_REDACTED]")
                return re.sub(r'([?&](?:key|api_key)=)[^&\s"\']+', r'\1[API_KEY_REDACTED]', item, flags=re.I)
            if isinstance(item, dict):
                return {k: clean(v) for k, v in item.items()}
            if isinstance(item, list):
                return [clean(v) for v in item]
            return item
        return clean(value)
