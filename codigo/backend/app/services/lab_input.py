"""Read bounded text only. Never extract a ZIP, fetch a repo or execute source code."""
import base64
import hashlib
from io import BytesIO
import json
from pathlib import PurePosixPath
import re
import stat
import zipfile

ALLOWED = {".py",".js",".jsx",".ts",".tsx",".json",".txt",".toml",".lock",".yaml",".yml"}
FORBIDDEN = {"node_modules",".git",".venv","venv","dist","build",".next","__pycache__"}

def safe_path(raw):
    if not isinstance(raw,str) or len(raw)>180 or not re.fullmatch(r"[A-Za-z0-9_. /@+-]+",raw):
        raise ValueError("Caminho inválido. Utilize nomes relativos simples.")
    parts=raw.split("/")
    if raw.startswith("/") or any(p in {"", ".", ".."} or p.lower() in FORBIDDEN or p.endswith(("."," ")) for p in parts):
        raise ValueError("Caminho fora do projeto ou pasta excluída.")
    if any(p.lower().startswith(".env") or p.lower() in {"credentials.json","id_rsa","id_ed25519"} for p in parts):
        raise ValueError("Ficheiros de credenciais não são aceites.")
    if PurePosixPath(raw).suffix.lower() not in ALLOWED:
        raise ValueError("Tipo de ficheiro não suportado.")
    return raw

def scrub(text):
    """Best-effort data minimization, not a guarantee that arbitrary secrets are detectable."""
    def blank_pem(m): return "[SEGREDO OMITIDO]"+"\n"*m.group(0).count("\n")
    text=re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",blank_pem,text,flags=re.S)
    # Preserve lines and executable context; replace quoted literal values near secret names.
    text=re.sub(r'''(?i)((?:password|passwd|secret|token|api[_-]?key|authorization|database_url)[\w"' ]*\s*[:=]\s*)(["'])([^\r\n]*?)\2''',r'\1\2[SEGREDO OMITIDO]\2',text)
    text=re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]{8,}",r"\1[SEGREDO OMITIDO]",text)
    text=re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{20,})\b","[SEGREDO OMITIDO]",text)
    text=re.sub(r"(?i)(https?|postgres(?:ql)?|mysql)://[^\s/@:]+:[^\s/@]+@",r"\1://[SEGREDO OMITIDO]@",text)
    text=re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}","[EMAIL OMITIDO]",text)
    return text

def prepare(data):
    entries=[(f.path,f.content) for f in data.files]
    if data.zip_base64:
        if entries: raise ValueError("Escolha ficheiros ou ZIP, não ambos.")
        try:
            raw=base64.b64decode(data.zip_base64,validate=True)
            if len(raw)>1_000_000: raise ValueError()
            with zipfile.ZipFile(BytesIO(raw)) as z:
                infos=z.infolist()
                if not infos or len(infos)>60 or sum(i.file_size for i in infos)>150_000: raise ValueError()
                for info in infos:
                    if info.is_dir(): continue
                    safe_path(info.filename)
                    mode=info.external_attr>>16
                    if stat.S_ISLNK(mode) or info.flag_bits&1 or info.file_size>30_000 or info.file_size>max(1000,info.compress_size*100): raise ValueError()
                    entries.append((info.filename,z.read(info).decode("utf-8")))
        except (ValueError,UnicodeError,zipfile.BadZipFile,RuntimeError,NotImplementedError):
            raise ValueError("ZIP inválido, excluído ou acima dos limites. Envie apenas código UTF-8, sem dependências nem credenciais.") from None
    if not entries or len(entries)>40: raise ValueError("Envie entre 1 e 40 ficheiros.")
    files,seen,total=[],set(),0
    for path,content in entries:
        safe_path(path)
        if path.casefold() in seen: raise ValueError("Caminhos repetidos não são aceites.")
        seen.add(path.casefold())
        if "\0" in content or any(ord(c)<32 and c not in "\r\n\t" for c in content): raise ValueError("Conteúdo binário não é aceite.")
        content=content.replace("\r\n","\n").replace("\r","\n")
        total+=len(content.encode("utf-8"))
        if total>150_000 or len(content.encode("utf-8"))>30_000: raise ValueError("Limite de 30 KB por ficheiro e 150 KB por projeto.")
        clean=scrub(content)
        files.append({"path":path,"content":clean,"lines":len(content.splitlines()) or 1,"sha256":hashlib.sha256(content.encode()).hexdigest(),"redacted":clean!=content})
    files.sort(key=lambda f:f["path"])
    digest=hashlib.sha256(json.dumps([(f["path"],f["sha256"]) for f in files],separators=(",",":")).encode()).hexdigest()
    return files,digest
