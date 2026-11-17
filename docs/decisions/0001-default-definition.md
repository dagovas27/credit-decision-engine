# ADR 0001 — Default definition for the PD label

- **Status:** Accepted
- **Date:** 2026-11-17
- **Affects:** `gold.default_labels` (week 4), model training (week 5), expected profit (week 6)

## Context

The PD model needs one binary label per loan. The Freddie Mac performance file reports a
monthly delinquency status (`00`, `01`, `02`, `03`, … up to `99`, `RA` for REO acquisition,
`XX` not available) and, in the final record, a zero-balance code that explains why the loan
left the dataset. A loan can leave the dataset through a **credit event** (third-party sale,
short sale/charge-off, REO disposition, whole-loan sale) without ever being reported as
90+ days delinquent in an earlier month, so a label based only on the delinquency status
would miss some real defaults. A loan can also prepay before it has had time to default.

## Decision

A loan is a **default (label = 1)** if, within its **24-month observation window**, the
**first** of these events happens:

| Event | Field | Values |
| --- | --- | --- |
| 90+ days delinquent | Current Loan Delinquency Status (field 4) | numeric value `>= 03` |
| REO acquisition | Current Loan Delinquency Status (field 4) | `RA` |
| Credit-event termination | Zero Balance Code (field 9) | `02`, `03`, `09`, `15` |

A loan is a **non-default (label = 0)** if none of those events happens in the window. In
particular, a loan that **prepays (zero-balance code `01`) before any default event** is a
non-default, even if the prepayment happens before month 24.

### Precise rules

1. **Observation window.** Months `first_payment_date` through `first_payment_date + 23
   months`, using the *First Payment Date* from the origination file and the *Period* of each
   performance record. We do not use *Loan Age*, because Freddie Mac resets it when a loan is
   modified.
2. **Eligibility.** Only loans whose full window is observed are labelled:
   `first_payment_date + 23 months <= 2026-06` (the performance cut-off of Release 48).
   Loans with an incomplete window are not labelled; they feed the "production" simulation.
3. **First event wins.** Records are ordered by *Period*. The label and the event month are
   taken from the first record in the window that matches a default event. Later cures do
   not change the label.
4. **Other terminations.** A loan that leaves the dataset with any other code (`01`
   prepaid/matured, `16` reperforming-loan securitisation, `96` defect before a credit
   event) before a default event is a non-default.
5. **Unknown status.** `XX` (not available) is not a default event.
6. **Stored with the label:** `default_flag`, `default_month` (Period of the first event),
   `default_trigger` (`DQ90`, `RA` or `ZB_<code>`) and `months_to_default`, so that the
   definition can be audited and changed later without re-reading Bronze.

## Alternatives considered

- **90+ days delinquent only.** Simpler, but misses loans that go straight to a short sale
  or third-party sale, which are exactly the costliest outcomes for the profit layer.
- **Exclude loans that prepay before month 24.** Avoids labelling a loan as "good" before it
  has been fully observed, but drops a large and non-random share of loans (refinance waves
  in 2012 and 2020–2021) and makes the training sample unrepresentative of the applications
  the engine will see. Survival models handle this censoring properly; they are out of scope
  for the 8-week plan.

## Consequences

- Prepayment is treated as a good outcome. In years with heavy refinancing, many loans are
  labelled 0 after only a few months, which lowers the observed default rate. This is
  consistent with the business question (the loan did not cause a loss), and the expected
  profit layer must account for the shorter life of those loans.
- The label depends on the performance cut-off date; any new data release must recompute
  eligibility.
- COVID-era forbearance (vintages 2019–2021) can trigger the `>= 03` rule for borrowers who
  later cure without loss. How to treat those cases is an open question for week 4 (see
  `docs/PROGRESS.md`); this ADR does not change the rule for them yet.
