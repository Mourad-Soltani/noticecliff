# NoticeCliff

Signature: Mourad.Soltani

NoticeCliff is a tiny local tool that answers one question: what is the last calendar day you can still send a cancellation notice before a subscription auto-renews?

Solo operators and finance ops teams paste a renewal date and a contractual notice window. NoticeCliff returns the cancel-by date, days remaining, and a risk band. It does not email vendors, cancel accounts, or store contracts.

## Why this exists

Auto-renew clauses hide the real decision date. The renewal date is not the deadline. The deadline is renewal date minus the notice window, and some contracts count that window in business days. Spreadsheets get this wrong on weekends.

## Run

Python 3.11+ and the standard library only.

```bash
python3 -m noticecliff.cli --renewal 2026-12-01 --notice-days 30 --as-of 2026-10-01
python3 -m noticecliff.server --port 8765
curl -s localhost:8765/health
```

POST `/v1/cliff` with JSON:

```json
{"renewal_date":"2026-12-01","notice_days":30,"count_mode":"calendar","buffer_days":0,"as_of":"2026-10-01"}
```

`count_mode` is `calendar` or `business`. Business mode skips Saturday and Sunday. It does not include public holidays unless you pass `skip_dates`.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Limits

This is a date calculator, not legal advice. Confirm notice method (email, certified mail) and whether the contract counts the renewal day itself. Default rule: notice must be received strictly before the renewal date, so the window ends the day before renewal minus `notice_days` steps.

## License

MIT. Copyright (c) 2026 Mourad.Soltani
