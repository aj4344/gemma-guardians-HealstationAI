"""ASGI middleware: request ids, response headers (API-03), body-size limits (INV-9)."""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from healstation.security.context import begin_sensitive_scope, end_sensitive_scope, reset_request_id, set_request_id

# No external origins: the UI, its fonts and its scripts are all served locally.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; media-src 'self' blob:; font-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'"
)
SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(self), microphone=(self), geolocation=(self), payment=(), usb=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}
_CLIENT_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


class RequestContextMiddleware:
    """Assigns a request id and adds no-store and security headers to every response."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        supplied = dict(scope.get("headers") or []).get(b"x-request-id", b"").decode("latin-1")
        request_id = supplied if _CLIENT_REQUEST_ID.fullmatch(supplied) else uuid.uuid4().hex
        token = set_request_id(request_id)
        sensitive_token = begin_sensitive_scope()
        is_api = scope.get("path", "").startswith("/api")

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                for name, value in SECURITY_HEADERS.items():
                    headers.setdefault(name, value)
                if is_api:
                    # Responses carry patient data: never store them in any cache.
                    headers["Cache-Control"] = "no-store"
                    headers["Pragma"] = "no-cache"
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            end_sensitive_scope(sensitive_token)
            reset_request_id(token)


class BodySizeLimitMiddleware:
    """Refuses bodies over the route's limit — declared or streamed (chunked).

    A declared Content-Length over the limit is refused before reading. A
    streamed body is cut off at the limit: the app sees the body end early,
    and whatever it answers is replaced with the 413 response.
    """

    def __init__(self, app: ASGIApp, limit_for: Callable[[Scope], int], on_too_large: Callable[[Scope], ASGIApp]):
        self.app = app
        self.limit_for = limit_for
        self.on_too_large = on_too_large

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = self.limit_for(scope)
        declared = dict(scope.get("headers") or []).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > limit:
            await self.on_too_large(scope)(scope, receive, send)
            return

        received = 0
        too_large = False

        async def counting_receive() -> Message:
            nonlocal received, too_large
            if too_large:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    too_large = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        async def guarded_send(message: Message) -> None:
            if not too_large:
                await send(message)

        await self.app(scope, counting_receive, guarded_send)
        if too_large:
            await self.on_too_large(scope)(scope, receive, send)
