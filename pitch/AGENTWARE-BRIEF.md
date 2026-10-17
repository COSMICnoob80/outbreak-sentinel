# Agentware Brief — Outbreak Sentinel (Nov 27–30, 72h, Open Track)

## The brief

"Build an agent you can walk away from — prove it knows when to stop."
Solo welcome. $1,800 cash across six tracks. 72 hours. Prizes include Best Kill Switch ($100).

## Our answer in one line

An agent that buys ranked intelligence through Telegraph, fuses it into a calibrated
risk card, issues a signed receipt, and resolves it later against reality — and that
*cannot* escalate a card on a single signal, cannot spend real money (testnet only),
and cannot rewrite its own history.

## The receipt ledger as the trust mechanism

Agentware's core question is "how do you know the agent did what it claims?" Our
answer is the ledger, not a log line:

- Every `HIGH`/`CRITICAL` card becomes a receipt: id = sha256 of the card's content.
- The ledger is append-only JSONL (`history/receipts.jsonl`); there is no edit or
  un-resolve helper in the codebase. Resolution appends a new event.
- `/scoreboard` is the honest track record: calls made, resolved, verdicts.
- `resolved: 0` is a feature — we only count what a human checked against a real source.

That is what lets a judge (or an operator) walk away: the agent's track record is
auditable after the fact, not asserted in a README.

## Kill-switch story (Best Kill Switch, $100)

Three independent kill switches, all enforced in code, not in policy:

1. **Calibration gate.** `HIGH` requires ≥ 2 independent signal families to agree.
   A single noisy source can never escalate a card. One signal is never enough —
   written into the calibration rule, not a prompt.
2. **Testnet boundary.** Telegraph settlement runs on Base Sepolia (chain id 84532)
   with a mocked settlement leg; `TESTNET_BOUNDARY` is printed on screen unprompted
   and `is_live()` is false unless a wallet is configured. No real value moves.
3. **Human resolver.** Resolution is human-in-the-loop by design: a receipt is only
   scored when a person runs `verify.py <id> CONFIRMED|REFUTED "<source>"`.
   The agent never self-scores.

Plus the operational kill switches: rule-based fallback when the LLM is unavailable
(no silent fabrication), and `POST /alerts` fan-out that can be left unconfigured
so nothing ships.

## Near-miss write-up angle

A real near-miss, already in our git history: on 2026-10-13 the ledger contained a
synthetic resolution event citing a source dated in the future relative to the
receipt's issue date ("DGHS Pakistan weekly bulletin 2026-11-07" against a
2026-10-13 receipt). We purged it by hand — `receipts.py` has no un-resolve or
rewrite helper, so the correction was a new event, not a mutation — and the ledger
now reads 1 line, `status: OPEN`, `resolved: 0`. That is the write-up: the agent
caught its own false confirmation, and the append-only property is what made the
fix auditable rather than cosmetic. (Verify the Agentware "near miss" category name
against the rules page before submitting; this is our proposed angle.)

## Submission checklist (Agentware)

- [ ] Agent runs end-to-end unattended for 72h (cron + ledger).
- [ ] Kill-switch demo: show a single-signal input that does NOT escalate.
- [ ] Near-miss write-up (above) included in submission.
- [ ] Receipt ledger + `/scoreboard` shown as the trust mechanism.
- [ ] $0 spend proof (Groq free tier, Oracle/Railway free, mocked settlement).