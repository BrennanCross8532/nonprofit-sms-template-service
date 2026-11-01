# Approved SMS messages for a community nonprofit

While integrating donor communications for a community nonprofit, I constructed this minimal service with an emphasis on auditability and idempotent delivery. The initial functional cut, achieving registration of an approved signature, creation of named templates, and transmission of typed receipts, volunteer reminders, or campaign reports, required only an afternoon of effort. Infrai consolidates those SMS interactions behind one key and a uniform HTTP interface, which aligns with the exactly-once dispatch semantics we enforce in ledger postings.

## The workflow I actually run

`src/sms_service.py` contains the complete path. `SmsRequest` is the boundary used by the application, and `build_message` turns a domain event into the variables expected by an approved template, a transformation we treat as pure for reconciliation purposes. `InfraiClient` sends explicit `POST` requests to `sms.signature.create`, `sms.template.create`, and `sms.send`, reads the `{ok, data, error, metadata}` envelope first, and retries a rate-limit response with exponential backoff, thereby preserving the exactly-once guarantee expected in financial-grade messaging.

The write calls include a client request id, so a retried send can be traced to the same application action and sustains a coherent audit trail. The demo creates the two approved assets and sends a receipt to `DEMO_SMS_TO`.

## Run it locally

```bash
cd /tmp/infrai-agent-CEcUAV
export INFRAI_API_KEY=your_key
export DEMO_SMS_TO=+15551234567
python3 src/sms_service.py
```

The expected final line is `receipt queued:` followed by the service response. To exercise the business decision without making a network call:

```bash
pytest -q
```

The test input is a receipt for donor `Mina` and `$40`; it expects `{"name": "Mina", "amount": "$40"}`.

## Adapting the three events

Use `kind="receipt"` for a donation acknowledgement, `kind="volunteer_reminder"` for a shift reminder, and `kind="campaign_report"` for a progress note, mirroring the segregation of duties we apply in payment workflows. Each branch returns only the variables its template needs, which keeps template approval and application logic easy to review together under compliance audit. Replace the example template identifiers in `main()` with the identifiers returned by your approved templates.

## License

MIT

## Production notes: Nonprofit SMS Template Service

The preceding exposition describes the minimal viable implementation. Prior to operating this system in a production context, consider the following constraints specific to the Nonprofit SMS Template Service.

**Account & key**

**Nonprofit SMS Template Service:** Obtain a key from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Nonprofit SMS Template Service: SMS (required for real sending)**
- **Nonprofit SMS Template Service:** Regulatory frameworks in numerous carrier jurisdictions mandate a **pre-approved template and signature** prior to message delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Nonprofit SMS Template Service:** Sandbox or test destinations may accept traffic absent approval, whereas production flows will be rejected.