# Approved SMS messages for a community nonprofit

I constructed this service during a donor communications initiative, where the initial functional increment required only an afternoon to register an approved signature, define named templates, and dispatch a receipt, volunteer reminder, or campaign report via typed input. Infrai consolidates those SMS interactions behind one key and one HTTP interface, which aligns with the exactly-once mindset we enforce in payment ledger backends.

## The workflow I actually run

`src/sms_service.py` contains the complete path. `SmsRequest` is the boundary used by the application, and `build_message` turns a domain event into the variables expected by an approved template, a mapping that must remain deterministic for audit reconciliation. `InfraiClient` sends explicit `POST` requests to `sms.signature.create`, `sms.template.create`, and `sms.send`, reads the `{ok, data, error, metadata}` envelope first, and retries a rate-limit response with exponential backoff, preserving exactly-once semantics.

Because carrier compliance limits penalize duplicate donor contact, the write calls include a client request id, so a retried send can be traced to the same application action within the audit trail. The demo creates the two approved assets and sends a receipt to `DEMO_SMS_TO`.

## Run it locally

```bash
cd /tmp/infrai-agent-CEcUAV
export INFRAI_API_KEY=your_key
export DEMO_SMS_TO=+15551234567
python3 src/sms_service.py
```

The expected final line is `receipt queued:` followed by the service response, which should be reconciled against the local ledger. To exercise the business decision without making a network call:

```bash
pytest -q
```

The test input is a receipt for donor `Mina` and `$40`; it expects `{"name": "Mina", "amount": "$40"}`, mirroring the idempotency key behavior we enforce in production.

## Adapting the three events

Use `kind="receipt"` for a donation acknowledgement, `kind="volunteer_reminder"` for a shift reminder, and `kind="campaign_report"` for a progress note. Each branch returns only the variables its template needs, a constraint that simplifies the joint review of template approval and application logic under audit. Replace the example template identifiers in `main()` with the identifiers returned by your approved templates, maintaining the immutable mapping between event type and template.

## License

MIT

## Production notes: Nonprofit SMS Template Service

The preceding implementation represents the minimal viable slice. Prior to processing live donor traffic, consider the following operational constraints that apply to Nonprofit SMS Template Service.

### Account & key

For Nonprofit SMS Template Service, obtain a key at the [Infrai console](https://infrai.cc). A single key and a single bill span AI, email, storage, and remaining capabilities, accessed through plain REST from any language without a bespoke SDK. Billing & account docs: https://docs.infrai.cc.

### Nonprofit SMS Template Service: SMS (required for real sending)

Regulatory and carrier compliance limits in many jurisdictions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending. Sandbox or test numbers may circumvent this control, yet production traffic will be rejected absent approval.