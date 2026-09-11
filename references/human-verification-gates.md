# Human verification gates

AI can draft, calculate, code, and audit, but it cannot certify facts or actions it did not directly observe. Record every such item in `HUMAN_TASKS.md` with an owner, deadline, evidence path, and status.

## Always human-owned

- Choose the final problem and approve the operational interpretation.
- Confirm that assumptions match domain reality and that recommendations are acceptable in context.
- Read the final paper, confirm authorship, sign required declarations, and submit through the official system.
- Perform any action that consumes a limited official attempt, binds the team, or requires personal credentials unless the user explicitly takes control at that moment.

## Human evidence required

- physical measurements, laboratory observations, field surveys, interviews, and expert judgments not present in supplied evidence;
- official simulator runs, hardware tests, licensed desktop software, authenticated portals, CAPTCHA, signatures, or irreversible submission actions;
- visual and semantic review of the final rendered paper and every required result file;
- confirmation that supporting archives open on a clean machine and contain no identity or private data;
- any claim whose correctness depends on local conditions, future events, or inaccessible proprietary data.

## AI may prepare but must not claim completion

AI may write test scripts, simulator clients, checklists, upload manifests, and step-by-step operator instructions. Mark the task `WAITING_FOR_HUMAN` until the human returns the actual log, screenshot, signed page, exported file, or other required evidence. Never replace missing evidence with a plausible narrative.

## Limited-attempt protocol

Before an official run or submission:

1. complete unlimited local or practice tests;
2. freeze code and configuration hashes;
3. prepare rollback and log capture;
4. ask the human operator to confirm the exact action;
5. record the returned official artifact without altering it.
