"""Local, human-entered provider configuration. No logging or network calls."""
import os
from pathlib import Path
import re
import tempfile

ALLOWED_KEYS = {"TAVILY_API_KEY", "GROQ_API_KEY", "URLHAUS_AUTH_KEY"}


def save_provider_keys(path: Path, updates: dict) -> list[str]:
    if not isinstance(updates, dict) or set(updates) - ALLOWED_KEYS:
        raise ValueError("Apenas as chaves de integração permitidas podem ser alteradas.")
    clean = {}
    for name, value in updates.items():
        if not isinstance(value, str):
            raise ValueError("Formato de chave inválido.")
        if not value.strip():
            continue
        key = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{16,512}", key):
            raise ValueError("Formato de chave inválido. Cola apenas a chave, sem aspas ou outros comandos.")
        clean[name] = key
    if not clean:
        raise ValueError("Introduz pelo menos uma chave. Campos vazios preservam a configuração existente.")
    if not path.is_file() or path.is_symlink():
        raise ValueError("Configuração local ausente. Executa primeiro scripts/setup_local.py.")
    original = path.read_bytes()
    text = original.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    output, seen = [], set()
    for line in text.splitlines(keepends=True):
        match = re.match(r"^\s*(?:export\s+)?([A-Z_]+)\s*=", line)
        name = match[1] if match else None
        if name in clean:
            if name not in seen:
                output.append(name + "=" + clean[name] + newline)
                seen.add(name)
        else:
            output.append(line)
    result = "".join(output)
    for name in sorted(clean.keys() - seen):
        if result and not result.endswith(("\r", "\n")):
            result += newline
        result += name + "=" + clean[name] + newline
    encoded = (b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b"") + result.encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".env.", suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            file.write(encoded)
            file.flush()
            os.fsync(file.fileno())
        # Reject concurrent edits rather than overwriting another configuration change.
        if path.read_bytes() != original:
            raise ValueError("A configuração mudou entretanto. Fecha outras edições e tenta novamente.")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return sorted(clean)
