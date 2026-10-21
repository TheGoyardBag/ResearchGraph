"""Local configuration, safe serialization and SQLite persistence.

This is a single-operator demonstration. Shared tokens are NOT multi-user authentication.
"""
from __future__ import annotations
import hashlib, hmac, json, os, secrets, sqlite3, tempfile, uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import numpy as np
from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent / "assets"

def jsonable(value: Any) -> Any:
    if isinstance(value, dict): return {str(k):jsonable(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray): return jsonable(value.tolist())
    if isinstance(value, np.generic): return jsonable(value.item())
    if isinstance(value, Path): return str(value)
    if isinstance(value, float) and not np.isfinite(value): return None
    return value

def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(jsonable(value),indent=2,sort_keys=True,allow_nan=False)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f: f.write(text+"\n")
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)

def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest(folder: Path) -> None:
    dump(folder/"manifest.json", {p.name:digest(p) for p in sorted(folder.iterdir()) if p.is_file() and p.name!="manifest.json"})

def verify(folder: Path) -> None:
    if not (folder/"manifest.json").is_file(): raise ValueError("Missing artifact manifest. Run training first.")
    for name, expected in load(folder/"manifest.json").items():
        if Path(name).name != name or not (folder/name).is_file() or not hmac.compare_digest(digest(folder/name), expected):
            raise ValueError("Artifact checksum mismatch: "+name)
    # Manifest detects accidental changes, not a malicious replacement of both files and manifest.

@dataclass(frozen=True)
class Settings:
    state: Path
    token: str
    artifacts: Path = ASSETS / "artifacts"

    @classmethod
    def environment(cls) -> "Settings":
        state=Path(os.getenv("APP_STATE_DIR",ROOT/"var"))
        token=os.getenv("APP_TOKEN","").strip()
        token_file=state/"token"
        if not token and token_file.exists(): token=token_file.read_text().strip()
        return cls(state,token,Path(os.getenv("APP_ARTIFACTS",ASSETS/"artifacts")))

    def initialize(self) -> str:
        if self.token:
            return self.token
        self.state.mkdir(parents=True,exist_ok=True)
        path=self.state/"token"
        if not path.exists():
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,"w") as f: f.write(secrets.token_urlsafe(32)+"\n")
        return path.read_text().strip()

class Store:
    def __init__(self, folder: Path):
        folder.mkdir(parents=True,exist_ok=True)
        self.path=folder/"app.sqlite3"
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, kind TEXT NOT NULL, created TEXT NOT NULL, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), decision TEXT NOT NULL, note TEXT NOT NULL, created TEXT NOT NULL)")

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        db.row_factory=sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self,kind: str,payload: Any) -> str:
        key=uuid.uuid4().hex
        with self.connect() as db:
            db.execute("INSERT INTO events VALUES(?,?,?,?)",(key,kind,datetime.now(timezone.utc).isoformat(),json.dumps(jsonable(payload),allow_nan=False)))
        return key

    def get(self,key: str) -> dict:
        with self.connect() as db: row=db.execute("SELECT * FROM events WHERE id=?",(key,)).fetchone()
        if row is None: raise KeyError(key)
        return {**dict(row),"payload":json.loads(row["payload"])}

    def list(self,kind: str|None=None,limit: int=25) -> list[dict]:
        limit=max(1,min(int(limit),100))
        with self.connect() as db:
            rows=db.execute("SELECT * FROM events WHERE kind=? ORDER BY created DESC LIMIT ?",(kind,limit)).fetchall() if kind else db.execute("SELECT * FROM events ORDER BY created DESC LIMIT ?",(limit,)).fetchall()
        return [{**dict(r),"payload":json.loads(r["payload"])} for r in rows]

    def review(self,key: str,decision: str,note: str) -> None:
        if decision not in {"correct","incorrect","unsure"}: raise ValueError("Unknown review decision")
        if len(note)>2000: raise ValueError("Note too long")
        self.get(key)
        with self.connect() as db:
            db.execute("INSERT INTO reviews(event_id,decision,note,created) VALUES(?,?,?,?)",(key,decision,note,datetime.now(timezone.utc).isoformat()))


def authorization(settings: Settings):
    def check(authorization: str=Header(default="")):
        if not settings.token: raise HTTPException(503,"Run the setup command before serving.")
        expected="Bearer "+settings.token
        if not hmac.compare_digest(authorization.encode("utf-8"),expected.encode("utf-8")): raise HTTPException(401,"Valid bearer token required",headers={"WWW-Authenticate":"Bearer"})
    return check

async def security_headers(request: Request, call_next):
    content_length=request.headers.get("content-length")
    if content_length:
        try: length=int(content_length)
        except ValueError: return JSONResponse({"detail":"Invalid Content-Length"},status_code=400)
        if length>6_000_000: return JSONResponse({"detail":"Request too large"},status_code=413)
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Cache-Control"]="no-store"
    # Inline styles are allowed for locally generated chart geometry; scripts must be local.
    response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response
