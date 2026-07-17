"""Local authentication and role management for the BAIF worker."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


Role = Literal["admin", "user"]
Status = Literal["pending", "active", "deactivated"]

SESSION_COOKIE_NAME = "vaanisetu_session"
SESSION_TTL_SECONDS = 12 * 60 * 60
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 5
MAX_LOGIN_FAILURE_KEYS = 10_000
MAX_SESSIONS_PER_USER = 10
PBKDF2_ITERATIONS = 260_000


class AuthError(RuntimeError):
    """Raised when authentication or authorization fails."""


@dataclass
class UserRecord:
    username: str
    password_hash: str
    role: Role
    status: Status
    display_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    approved_at: str | None = None
    approved_by: str | None = None
    deactivated_at: str | None = None


@dataclass
class SessionRecord:
    session_id: str
    username: str
    csrf_token: str
    created_at: float
    expires_at: float


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_username(username: str) -> str:
    normalized = username.strip().lower()
    if len(normalized) < 3:
        raise AuthError("Username must be at least 3 characters.")
    if len(normalized) > 64:
        raise AuthError("Username is too long.")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-@")
    if any(character not in allowed for character in normalized):
        raise AuthError("Use letters, numbers, dot, dash, underscore, or @ in the username.")
    return normalized


def _validate_password(password: str) -> None:
    if len(password) < 10:
        raise AuthError("Password must be at least 10 characters.")
    if len(password) > 256:
        raise AuthError("Password is too long.")


def hash_password(password: str) -> str:
    _validate_password(password)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        iteration_count = int(iterations)
        if algorithm != "pbkdf2_sha256" or iteration_count != PBKDF2_ITERATIONS:
            return False
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
        if len(salt) != 16 or len(expected) != hashlib.sha256().digest_size:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iteration_count)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


class AuthStore:
    def __init__(self, path: Path, session_ttl_seconds: int = SESSION_TTL_SECONDS):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.session_ttl_seconds = session_ttl_seconds
        self._lock = threading.RLock()
        self._users: dict[str, UserRecord] = {}
        self._sessions: dict[str, SessionRecord] = {}
        self._failures: dict[str, list[float]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return
        users = payload.get("users", {})
        if not isinstance(users, dict):
            users = {}
        self._users = {}
        for username, record in users.items():
            if not isinstance(username, str) or not isinstance(record, dict):
                continue
            try:
                user = UserRecord(**record)
                normalized = _normalize_username(username)
            except (AuthError, TypeError):
                continue
            if (
                normalized != username
                or user.username != username
                or user.role not in {"admin", "user"}
                or user.status not in {"pending", "active", "deactivated"}
                or not isinstance(user.password_hash, str)
                or not isinstance(user.created_at, str)
                or not isinstance(user.display_name, str)
            ):
                continue
            self._users[username] = user
        current = time.time()
        self._sessions = {}
        sessions = payload.get("sessions", {})
        if not isinstance(sessions, dict):
            sessions = {}
        for session_id, record in sessions.items():
            if not isinstance(session_id, str) or not isinstance(record, dict):
                continue
            try:
                session = SessionRecord(**record)
                created_at = float(session.created_at)
                expires_at = float(session.expires_at)
                is_current = expires_at > current and created_at <= expires_at
            except (TypeError, ValueError):
                continue
            if (
                is_current
                and session.session_id == session_id
                and session.username in self._users
                and isinstance(session.csrf_token, str)
                and bool(session.csrf_token)
            ):
                session.created_at = created_at
                session.expires_at = expires_at
                self._sessions[session_id] = session

    def _persist(self) -> None:
        payload = {
            "users": {username: asdict(record) for username, record in self._users.items()},
            "sessions": {session_id: asdict(record) for session_id, record in self._sessions.items()},
        }
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def setup_required(self) -> bool:
        with self._lock:
            return not any(user.role == "admin" for user in self._users.values())

    def create_first_admin(self, username: str, password: str, display_name: str = "") -> tuple[UserRecord, SessionRecord]:
        username = _normalize_username(username)
        with self._lock:
            if not self.setup_required():
                raise AuthError("First admin has already been created.")
            user = UserRecord(
                username=username,
                password_hash=hash_password(password),
                role="admin",
                status="active",
                display_name=display_name.strip()[:120],
                approved_at=_now_iso(),
                approved_by=username,
            )
            self._users[username] = user
            session = self._create_session_locked(username)
            self._persist()
            return user, session

    def register_user(self, username: str, password: str, display_name: str = "") -> UserRecord:
        username = _normalize_username(username)
        with self._lock:
            if self.setup_required():
                raise AuthError("Create the first admin before registering users.")
            if username in self._users:
                raise AuthError("A user with this username already exists.")
            user = UserRecord(
                username=username,
                password_hash=hash_password(password),
                role="user",
                status="pending",
                display_name=display_name.strip()[:120],
            )
            self._users[username] = user
            self._persist()
            return user

    def _create_session_locked(self, username: str) -> SessionRecord:
        current = time.time()
        expired = [session_id for session_id, session in self._sessions.items() if session.expires_at <= current]
        for session_id in expired:
            self._sessions.pop(session_id, None)
        user_sessions = sorted(
            (session for session in self._sessions.values() if session.username == username),
            key=lambda session: session.created_at,
        )
        while len(user_sessions) >= MAX_SESSIONS_PER_USER:
            oldest = user_sessions.pop(0)
            self._sessions.pop(oldest.session_id, None)
        session = SessionRecord(
            session_id=secrets.token_urlsafe(32),
            username=username,
            csrf_token=secrets.token_urlsafe(32),
            created_at=current,
            expires_at=current + self.session_ttl_seconds,
        )
        self._sessions[session.session_id] = session
        return session

    def _prune_failures_locked(self, key: str) -> list[float]:
        cutoff = time.time() - LOGIN_WINDOW_SECONDS
        failures = [timestamp for timestamp in self._failures.get(key, []) if timestamp >= cutoff]
        self._failures[key] = failures
        return failures

    def _bound_failure_cache_locked(self) -> None:
        cutoff = time.time() - LOGIN_WINDOW_SECONDS
        for key in list(self._failures):
            retained = [timestamp for timestamp in self._failures[key] if timestamp >= cutoff]
            if retained:
                self._failures[key] = retained
            else:
                self._failures.pop(key, None)
        while len(self._failures) > MAX_LOGIN_FAILURE_KEYS:
            oldest_key = min(self._failures, key=lambda item: self._failures[item][-1])
            self._failures.pop(oldest_key, None)

    def login(self, username: str, password: str, throttle_key: str = "") -> tuple[UserRecord, SessionRecord]:
        username = _normalize_username(username)
        key = f"{throttle_key}:{username}"
        with self._lock:
            failures = self._prune_failures_locked(key)
            if len(failures) >= LOGIN_MAX_FAILURES:
                raise AuthError("Too many failed sign-in attempts. Try again in 15 minutes.")
            user = self._users.get(username)
            if not user or not verify_password(password, user.password_hash):
                failures.append(time.time())
                self._failures[key] = failures
                self._bound_failure_cache_locked()
                raise AuthError("Username or password is incorrect.")
            if user.status == "pending":
                raise AuthError("Your account is waiting for admin approval.")
            if user.status == "deactivated":
                raise AuthError("This account has been deactivated.")
            session = self._create_session_locked(username)
            self._failures.pop(key, None)
            self._persist()
            return user, session

    def logout(self, session_id: str | None) -> None:
        if not session_id:
            return
        with self._lock:
            self._sessions.pop(session_id, None)
            self._persist()

    def authenticate(self, session_id: str | None) -> tuple[UserRecord, SessionRecord]:
        if not session_id:
            raise AuthError("Sign in to continue.")
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise AuthError("Your session has expired. Sign in again.")
            if session.expires_at <= time.time():
                self._sessions.pop(session_id, None)
                self._persist()
                raise AuthError("Your session has expired. Sign in again.")
            user = self._users.get(session.username)
            if not user or user.status != "active":
                raise AuthError("This account is not active.")
            return user, session

    def require_csrf(self, session: SessionRecord, token: str | None) -> None:
        if not token or not hmac.compare_digest(session.csrf_token, token):
            raise AuthError("Security check failed. Refresh the page and try again.")

    def require_admin(self, session_id: str | None) -> tuple[UserRecord, SessionRecord]:
        user, session = self.authenticate(session_id)
        if user.role != "admin":
            raise AuthError("Admin access is required.")
        return user, session

    def approve_user(self, username: str, admin_username: str) -> UserRecord:
        username = _normalize_username(username)
        with self._lock:
            user = self._users.get(username)
            if not user:
                raise AuthError("User not found.")
            if user.status == "deactivated":
                raise AuthError("Reactivate is not supported. Create a new account if access is needed.")
            user.status = "active"
            user.approved_at = _now_iso()
            user.approved_by = admin_username
            self._persist()
            return user

    def deactivate_user(self, username: str, admin_username: str) -> UserRecord:
        username = _normalize_username(username)
        with self._lock:
            if username == admin_username:
                raise AuthError("You cannot deactivate your own admin account.")
            user = self._users.get(username)
            if not user:
                raise AuthError("User not found.")
            user.status = "deactivated"
            user.deactivated_at = _now_iso()
            expired_sessions = [
                session_id
                for session_id, session in self._sessions.items()
                if session.username == username
            ]
            for session_id in expired_sessions:
                self._sessions.pop(session_id, None)
            self._persist()
            return user

    def list_users(self) -> list[UserRecord]:
        with self._lock:
            return sorted(self._users.values(), key=lambda user: user.created_at)
