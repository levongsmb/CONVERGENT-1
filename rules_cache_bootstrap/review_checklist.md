# Rules Cache Review Checklist — Phase 0 Master

Cross-reference of every parameter family awaiting user sign-off. Each row
maps to a YAML in `federal/`, `california/`, `multistate/`, or the top-level.

Mark each row as:

- `[x]` — signed off (values correct as populated)
- `[c]` — corrected (values updated in the YAML with signoff record)
- `[?]` — needs re-sourcing (flag Claude Code to re-populate)

Phase 0 is not complete until every row is `[x]` or `[c]`.

## Federal

- [ ] `federal/individual_brackets.yaml` — §1 ordinary income brackets for the planning year
- [ ] `federal/standard_deduction.yaml` — §63(c) standard deduction
- [ ] `federal/amt_individual.yaml` — §55–59 AMT exemption, phaseout, rate
- [ ] `federal/niit.yaml` — §1411 thresholds
- [ ] `federal/additional_medicare.yaml` — §3101(b)(2)
- [ ] `federal/fica_wage_bases.yaml` — OASDI and HI wage bases (§3121(a)(1), §1401)
- [ ] `federal/futa.yaml` — §3301
- [ ] `federal/retirement_limits.yaml` — §402(g), §414(v), §415(c), §401(a)(17), §408(k), §408(p)
- [ ] `federal/estate_gift_gst.yaml` — §2010 exemption, §2503(b) annual exclusion, GST exemption
- [ ] `federal/salt_cap_obbba.yaml` — §164(b)(6) / OBBBA SALT cap $40K structure
- [ ] `federal/qbi_199a.yaml` — §199A thresholds, phaseout widths, SSTB threshold
- [ ] `federal/section_461l.yaml` — §461(l) excess business loss
- [ ] `federal/section_163j.yaml` — §163(j) small-corp §448(c) threshold
- [ ] `federal/section_448c.yaml` — §448(c) gross receipts threshold
- [ ] `federal/section_1202.yaml` — QSBS exclusion caps (OBBBA $15M / phased holding period)
- [ ] `federal/section_1411_niit.yaml` — redundant marker; merged with `niit.yaml`
- [ ] `federal/section_6166.yaml` — §6166 installment election thresholds
- [ ] `federal/section_1045.yaml` — QSBS rollover parameters
- [ ] `federal/section_409a.yaml` — NQDC excise parameters
- [ ] `federal/capital_gain_brackets.yaml` — §1(h) 0/15/20% bracket breakpoints
- [ ] `federal/obbba_provisions_index.yaml` — master index of OBBBA §§ and their engine touchpoints

## California

- [ ] `california/ptet.yaml` — RTC §§ 19900 et seq. current rule (Decision 0004)
- [ ] `california/individual_brackets.yaml` — RTC §17041 brackets
- [ ] `california/amt.yaml` — CA AMT
- [ ] `california/mental_health_services_tax.yaml` — RTC §17043 1% above $1M
- [ ] `california/sdi_pfl.yaml` — SDI wage base, PFL rate
- [ ] `california/franchise_tax.yaml` — $800 minimum by entity type
- [ ] `california/conformity_adjustments.yaml` — CA nonconformity to federal (bonus, §179, §199A, OBBBA items)
- [ ] `california/nol.yaml` — CA NOL stacking and limitations

## Multistate

- [ ] `multistate/ptet_framework.yaml` — list of states with PTET elections in-scope for v1 (NY, NJ, MA, VA, CO)
- [ ] `multistate/apportionment_framework.yaml` — apportionment methodology map
- [ ] `multistate/residency_look_back.yaml` — residency-change look-back windows

## Top-level

- [ ] `obbba_notices.yaml` — enumerated Notices in bootstrapped snapshot (Decision 0003)
- [ ] `listed_transactions.yaml` — current IRS Listed Transaction designations
- [ ] `reportable_transactions.yaml` — current Reportable Transaction designations

## Master sign-off

When every row above is `[x]` or `[c]` the user records:

```
Signed off: <date> — <initials>
```

Claude Code reads the presence of that line and advances to Phase 1.
