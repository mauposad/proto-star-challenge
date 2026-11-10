# Research Ledger

This folder is the record of an EGM research dialogue: which critic raised
which finding and at what severity, what the Elephant proposed and why, what
the human decided, which findings are still open, and how each hypothesis
changed. The `egm-relator` agent writes the events; people and other tools
read them.

## Layout

| Path | Contents | Who writes it |
| :--- | :------- | :------------ |
| `events/<YYYYMMDDTHHMMSSZ>-<run>-<step>.jsonl` | One event per line (schema v1). Immutable once written. | `egm-relator` |
| `reports/<YYYYMMDDTHHMMSSZ>-<run>-<step>.md` | The Elephant's checkpoint report for that step: triage, reasons, decisions. | Elephant |
| `STATE.md` | Status board: open blockers, majors, and minors; decisions; each critic's record; hypotheses; discrepancies. Rebuilt by `ledger_state.py`. | Script |
| `TIMELINE.md` | The events as readable text, newest section last. | `egm-relator` |
| `snapshots/<YYYYMMDDTHHMMSSZ>-<purpose>.md` | Facts-only extracts given to Goldfish reviewers, with the selection rule. | Elephant (`egm-ledger snapshot`) |

## Rules

1.  **Immutable events**: Never edit or delete a file in `events/`. Correct the
    record with a new event (for example `finding.reopened`).
2.  **Provenance**: Every event says where it came from.
    `reported_by: artifact` events come from work products.
    `reported_by: elephant` events come from a checkpoint report and carry its
    words in `data.relayed`. Both cite their file in `evidence`.
3.  **Cross-checks**: When the Elephant's report and the work products
    disagree, the relator records `discrepancy.noted`. Nobody resolves it
    silently.
4.  **Order**: Event filenames sort chronologically. Read files in filename
    order and lines in file order.
5.  **Facts-only snapshots**: A snapshot for a Goldfish reviewer never includes
    `decision.recorded` or `discrepancy.noted` events, events reported by the
    Elephant, or `rationale` fields.

## Severity

Findings use the EGM scale: **Blocker**, **Major**, and **Nit** (minor).
`STATE.md` lists open findings under Open Blockers, Open Majors, and Open
Minors (Nits). A finding is open from `finding.raised` or `finding.reopened`
until a later `fixed`, `contested`, `declined`, or `settled` event; an
`escalated` finding is open and awaiting a human decision.

## Event Types and `data` Fields

| Type | `subject` | `data` fields |
| :--- | :-------- | :------------ |
| `run.started`, `run.finished` | run ID | `skill`, `rounds` (optional) |
| `hypothesis.proposed` | `H<n>` or `U<n>` | `statement`, `round`, `author` (agent or human) |
| `hypothesis.revised` | `H<n>` | `statement`, `round`, `answers` (finding IDs) |
| `hypothesis.merged` | new `H<n>` | `statement`, `round`, `merged_from` (IDs) |
| `hypothesis.dropped` | `H<n>` | `round`, `reason` (as written) |
| `finding.raised` | finding ID | `severity` (Blocker, Major, Nit), `title`, `reviewer`, `scope`, `round` (required) |
| `finding.fixed`, `finding.contested`, `finding.escalated`, `finding.declined`, `finding.settled`, `finding.reopened` | finding ID | `round` (required), `rationale`, `relayed` |
| `reviewer.not_run` | critic name | `round` (required), `reason` |
| `source.added`, `source.removed` | source key | `citation`, `access` |
| `document.revised` | document path | `summary` (as written) |
| `decision.recorded` | what was decided on | `by` (human or elephant, required), `decision` (required), `relayed` |
| `discrepancy.noted` | finding, hypothesis, or critic | `claimed`, `observed` (both required) |
| `snapshot.created` | snapshot path | `purpose`, `rule`, `for` (reviewer) |

The machine-readable schema is `skills/egm-ledger/references/event.schema.json`
in the EGM Research plugin.

## External Consumers

Tools outside the plugin, such as a Graphiti sync process in a separate
repository, read `events/*.jsonl` in filename order and must not write here.
