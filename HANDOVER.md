# Handover

VaaniSetu is delivered as a managed local/on-prem worker for authorised BAIF staff. Normal jobs do not call paid APIs, silently download models or send content to hosted translation services. Field recipients use reviewed exports and verified offline packages rather than running the model stack themselves.

## Handover package

| Need | Primary resource |
| --- | --- |
| Install and certify a Windows worker | `SETUP.md`, `scripts/windows_acceptance.ps1` |
| Train users | `BAIF_ONBOARDING_RUNBOOK.html`, `USAGE.md` |
| Operate, recover and support | `OPERATIONS.md`, `scripts/operations.py` |
| Approve a release | `ACCEPTANCE.md`, `TESTING.md` |
| Understand constraints | `ARCHITECTURE.md`, `COMPATIBILITY.md` |
| Govern data and licences | `PRIVACY.md`, `LICENSING.md` |
| Present the solution | `DEMO.md`, `submission/VaaniSetu_Final_Hackathon_Deck.pptx` |

The privacy-safe impact view/export contains aggregate counts only. Multi-file batches remain sequential to preserve the single-worker CPU and memory boundary.

## Ownership

- BAIF administrator: accounts, readiness, retention, backups and routine recovery
- Trainer/reviewer: source selection, output review, correction and approval
- Language reviewers: Hindi/Marathi terminology, transcript and translation sign-off
- BAIF IT: machine, model inventory, network controls, upgrade and restore approval
- Implementation team: reproducible defects and model/setup escalation

## Completion criteria

Knowledge transfer is complete when BAIF can independently:

1. install and pass preflight on the supported Windows worker;
2. approve a trainer and complete the three acceptance personas;
3. process and review the required BAIF video cases;
4. verify a package without the server/network;
5. create and restore a disposable backup; and
6. produce and inspect a privacy-safe support bundle.

Record the release commit, machine profile, model inventory, reviewers, operational owners and unresolved limitations. Tag the production release only after every external item in `ACCEPTANCE.md` is evidenced.

## Known boundaries

- Machine output is a draft until the appropriate reviewer approves it.
- NLLB is a non-commercial engineering fallback and cannot support an unrestricted production claim.
- Optional natural speech depends on the locally cached voice model; text/subtitles remain the dependable baseline.
- Cancellation is cooperative and takes effect at a processing boundary; active native model calls are not force-killed.
- The balanced laptop profile is the supported default. Use `quality` only after a representative-media benchmark; do not switch production workers to large-v3 by assumption.
