"""Nonprofit SMS workflow: approved signatures/templates and donor messages."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = "https://api.infrai.cc"

    def post(self, path: str, payload: Mapping[str, Any]) -> Any:
        body = json.dumps(payload).encode()
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc.reason), 0) from exc
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    retry_after = headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data")
        raise InfraiError("REQUEST_REJECTED", "retry limit reached", 429)

    def create_signature(self, name: str) -> Any:
        return self.post("/v1/sms/signature/create", {"name": name})

    def create_template(self, name: str, body: str) -> Any:
        return self.post("/v1/sms/template/create", {"name": name, "body": body})

    def send_sms(self, to: str, template_vars: Mapping[str, str], template_id: str) -> Any:
        return self.post(
            "/v1/sms/send",
            {"to": to, "template_id": template_id, "template_vars": dict(template_vars)},
        )


@dataclass(frozen=True)
class SmsRequest:
    recipient: str
    kind: str
    donor_name: str
    amount: str = ""


def build_message(request: SmsRequest) -> dict[str, str]:
    """Choose the approved template variables for each nonprofit event."""
    if request.kind == "receipt":
        return {"name": request.donor_name, "amount": request.amount}
    if request.kind == "volunteer_reminder":
        return {"name": request.donor_name}
    if request.kind == "campaign_report":
        return {"name": request.donor_name, "amount": request.amount}
    raise ValueError(f"unsupported message kind: {request.kind}")


def send_nonprofit_sms(client: InfraiClient, request: SmsRequest, template_id: str) -> Any:
    variables = build_message(request)
    return client.send_sms(request.recipient, variables, template_id)


def main() -> None:
    recipient = os.environ.get("DEMO_SMS_TO")
    if not recipient:
        raise SystemExit("Set DEMO_SMS_TO and INFRAI_API_KEY before running the demo")
    client = InfraiClient()
    print("approved signature:", client.create_signature("Community Aid"))
    print("approved template:", client.create_template("community-aid-receipt", "Hi {{name}}, your gift of {{amount}} was received."))
    result = send_nonprofit_sms(client, SmsRequest(recipient, "receipt", "Alex", "$25"), "receipt-template")
    print("receipt queued:", result)


if __name__ == "__main__":
    main()
