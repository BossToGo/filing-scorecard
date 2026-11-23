

# Member B test evidence

## Publication refresh, 23 November 2026

Greg explicitly requested shipping the previously reviewed S5 work. Refreshed against latest main
`cbd6957`: **541 tests passed** with real `.env` and external networking guarded. Only B-owned
implementation/tests, these evidence notes and Greg's appended AI-use entries are in the S5 change.
The pull request is a technical draft: personal Appendix A sign-off, Explain-back and teammate review
are still required. The shared plan/acceptance update is handed to A; no human check is invented.

## Stress-audit repairs, 22 November 2026

Greg requested all fixes in his own Part B files. The prepared S5 branch now passes **540 tests**
(42 past-performance tests). Its new regressions failed first at P4/P5/P6 and the 349/380-day
boundaries. No existing test expectation, default threshold or Appendix A sign-off was changed.
The S4 provenance repair and S6 health repairs are prepared in their separate owner branches.

Independent arithmetic for the new cases (labelled synthetic, not Appendix A):

- P6: `99,999,999/100,000,000 - 99,999,998/99,999,999 = 1/9,999,999,900,000,000 > 0`.
  The increasing order passes; the reversed order fails, even when displayed floats tie.
- P4/P5: `1/3 - 0.3333333333333333 = 1/30,000,000,000,000,000 > 0`. The supplied decimal
  benchmark cell is slightly below mathematical one-third. Exact equality with a benchmark still fails.
- Annual flows use `(end-start).days` in the existing resolver's inclusive numeric range 350–380;
  349 and 381 are unavailable, while 350, 379 and 380 are accepted. This fixes B's extra `+1`,
  following A's existing implementation without changing it or the SPEC's numeric bounds.

A separate stdlib Fraction computation, importing no application code, reproduced each identity
before the new results were accepted. Decisions use exact products/rationals; ratios remain floats
for display and retain the existing finite-range/missing-data protections. Filed input numbers are
compared using their decimal spelling, consistently with published benchmark/settings thresholds.

Independent code review caught a mistake in the first repair: direct Fraction conversion of binary
float amounts could disagree with decimal thresholds. Nine new regressions failed before the
consistent decimal helper was added. S5's four cases establish that `0.10/1 = 0.10` for P4/P5,
`0.1, 0.5, 2.5, 12.5, 62.5` is constant fivefold growth (P3 fails), and
`0.9/(0.6-0.3) = 0.3/(0.2-0.1) = 3` (P6 fails). Code and test re-reviews passed;
the test reviewer independently reproduced the equalities using Decimal arithmetic and verified
that no existing test function or expected value changed. All **669 combined tests** pass; the
36,000-status stress run and all original B-owned audit probes pass. The five saved companies'
18-check API journey passes; no actual screen/browser/visual check is claimed.

Owner A handoff: add these written workings/results to the shared acceptance/progress records,
record the elapsed-day alignment, and retain S5 as implementation prepared / personal sign-off
pending. A owns those documents; B has not edited them. D still owns the actual screen integration.

## Latest-main refresh, 22 November 2026

`b/S5-past-checks-ready` is based on current main `ab86bf0`; the full suite passes **527 tests**.
Combined current main + published S4 + prepared S5/S6 + reviewed S7 passes **639 tests**. The network-blocked
API journey returns all 18 checks for each of the five companies and preserves the specified Apple,
McDonald's and Amazon states, unavailable industry states and B's still-locked human expected answers.
This is draft publication evidence, not the required personal numerical sign-off or a browser check.

## S5: past-performance checks, draft pending personal sign-off

Prepared on 22 November 2026 on `b/S5-past-checks`. `past_checks(company, settings=section,
benchmarks=industry_facts)` returns P1-P6 in order. The settings argument is
`load_settings()["past_performance"]`; the benchmark argument is a mapping from `roe` and
`operating_margin` to sourced `Fact` objects. Passing no benchmarks leaves P4/P5 unassessed.
The helper `_b_inputs.py` belongs to B and is also intended for S6; it has no files or network access.

Tests cite SPEC §7's rules and boundaries and use labelled synthetic inputs that are not Appendix A.
They cover strict comparisons, missing years, zero/negative denominators and equity, losses,
benchmark provenance, USD units, annual periods including 53-week years, cover-page share dates,
currency-scaling invariance and empty data. They do not use or unlock the fixture's expected values.
Greg's P/H calculation and A's recording of his sign-off remain prerequisites for known-answer
acceptance; this slice must not be described as accepted or merge-ready without them.

Tests first: the missing `src.checks.past` import was observed before implementation. A subsequent
benchmark-key mismatch test was observed failing before validation was added. The architecture test
caught Codex using a dynamic date import, which was replaced with an ordinary import. No existing
test or financial expected value was changed. During preparation Codex removed its own passing
test that unnecessarily assumed B's sign-off would remain absent forever; A's tests already cover
the sign-off gate. The production code never reads or changes that gate.

Fiscal years are selected using annual distances (350-380 days per interval, SPEC §5.3), never by
compressing gaps. All displayed input Facts preserve their sources. Ratios stay decimal and are
not rounded for pass/fail. A check that cannot form a finite ratio reports insufficient data.

Read-only code and test reviews found a P3 tie-rounding bug: a constant fivefold annual growth sequence
could pass because the displayed compound rate was slightly below the latest rate. A regression failed
first; the decision now compares exact rational values using the equivalent inequality
`NI0^3 * NI-4 > NI-1^4`. Floating-point output is retained for display only. New properties test nonzero
geometric growth, acceleration/deceleration and P4's invariance when opening/closing equity is redistributed
with the same sum. Review also found P6 could turn an overflowing capital subtraction into a finite zero
return; a failing regression preceded a finite-intermediate guard. Both reviewers accepted the fixes.
The test reviewer requested removing an internal project-status phrase from the latest-loss explanation;
only the financial reason remains in the returned result.

Policy agreed by Greg in chat on 22 November 2026: when only FY0 is a loss, P3 reports insufficient data
because the four-year compound growth is undefined. A regression records the distinction from §7's
explicit failure when FY-4 or FY-1 is nonpositive. A should record this clarification in the shared SPEC
and architecture decision log; B has not edited those A-owned files.

Final evidence: full S5 suite 487 passed; combined S4/S5/S6 suite 546 passed. The offline B API journey ran
12 P/H checks for each of the five saved demo companies, plus unknown-industry and missing-revenue cases.
The network guard recorded zero external attempts. No UI or browser check is claimed.

Owner A handoff: update S5 to implementation prepared / personal sign-off pending, record test
results after the final run, and reconcile the older acceptance document with SPEC v2.4. B has
not edited A's product/acceptance/plan files or the synthetic fixture. D owns interface integration;
no browser check or screenshot inspection is claimed for this logic-only draft.
