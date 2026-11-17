"""Read-only access to a mailbox over IMAP.

Works with Gmail, Outlook, Yahoo, iCloud and most providers. The mailbox is
opened read-only, so reading never marks messages as read, and nothing is
ever sent or deleted.
"""

import email
import html
import imaplib
import re
from email.header import decode_header, make_header
from email.policy import default as default_policy

from . import config

MAX_BODY_CHARS = 8000


class EmailNotConfigured(Exception):
    pass


def _connect(folder: str) -> imaplib.IMAP4_SSL:
    if not config.email_configured():
        raise EmailNotConfigured(
            "Email is not set up. Add EMAIL_ADDRESS and EMAIL_APP_PASSWORD to your .env file."
        )
    conn = imaplib.IMAP4_SSL(config.IMAP_SERVER, config.IMAP_PORT)
    conn.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
    status, _ = conn.select(_quote(folder), readonly=True)
    if status != "OK":
        conn.logout()
        raise ValueError(f"Folder not found: {folder}")
    return conn


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _header(value) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\n\s*\n+", "\n\n", html.unescape(raw)).strip()


def _body_text(msg) -> str:
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    try:
        content = part.get_content()
    except Exception:
        payload = part.get_payload(decode=True) or b""
        content = payload.decode(errors="replace")
    if part.get_content_type() == "text/html":
        content = _html_to_text(content)
    return content.strip()


def _summaries(conn, uids: list[bytes]) -> list[dict]:
    results = []
    for uid in uids:
        status, data = conn.uid(
            "FETCH", uid, "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
        )
        if status != "OK" or not data or not isinstance(data[0], tuple):
            continue
        flags = data[0][0].decode(errors="replace")
        headers = email.message_from_bytes(data[0][1], policy=default_policy)
        results.append(
            {
                "id": uid.decode(),
                "from": _header(headers.get("From")),
                "subject": _header(headers.get("Subject")) or "(no subject)",
                "date": _header(headers.get("Date")),
                "unread": "\\Seen" not in flags,
            }
        )
    return results


def list_emails(count: int = 10, unread_only: bool = False, folder: str = "INBOX") -> list[dict]:
    """Newest emails first."""
    conn = _connect(folder)
    try:
        status, data = conn.uid("SEARCH", None, "UNSEEN" if unread_only else "ALL")
        uids = data[0].split() if status == "OK" and data and data[0] else []
        return _summaries(conn, list(reversed(uids[-count:])))
    finally:
        conn.logout()


def search_emails(query: str, count: int = 10, folder: str = "INBOX") -> list[dict]:
    """Emails whose sender, subject or body contain the query text."""
    conn = _connect(folder)
    try:
        conn.literal = query.encode("utf-8")
        status, data = conn.uid("SEARCH", "CHARSET", "UTF-8", "TEXT")
        uids = data[0].split() if status == "OK" and data and data[0] else []
        return _summaries(conn, list(reversed(uids[-count:])))
    finally:
        conn.logout()


def read_email(email_id: str, folder: str = "INBOX") -> dict:
    conn = _connect(folder)
    try:
        status, data = conn.uid("FETCH", email_id.encode(), "(BODY.PEEK[])")
        if status != "OK" or not data or not isinstance(data[0], tuple):
            raise ValueError(f"No email with id {email_id}")
        msg = email.message_from_bytes(data[0][1], policy=default_policy)
        body = _body_text(msg)
        if len(body) > MAX_BODY_CHARS:
            body = body[:MAX_BODY_CHARS] + "\n\n[... email continues, shortened ...]"
        attachments = [p.get_filename() for p in msg.iter_attachments() if p.get_filename()]
        return {
            "id": email_id,
            "from": _header(msg.get("From")),
            "to": _header(msg.get("To")),
            "subject": _header(msg.get("Subject")),
            "date": _header(msg.get("Date")),
            "attachments": attachments,
            "body": body,
        }
    finally:
        conn.logout()
