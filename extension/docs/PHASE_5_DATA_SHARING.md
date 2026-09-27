# Phase 5 carry-forward: one data-sharing mechanism, three tiers

> **Status: spec complete, implementation not started.** Nothing in this document is built. There is no MCP
> server, no `mcp/` folder, and no AI-assistant-facing code anywhere in this repository -- confirmed by
> direct search, not inferred from commit history. This file records the requirements Phase 5 must satisfy
> whenever it is built; it is not itself a feature, and shipping the rest of the extension around it does not
> change that status. See [README.md](../README.md)'s status line, which links back here.

Recorded from the project owner's instructions on 2026-09-27, so the Phase 5 (local MCP server) spec starts
from them instead of re-deriving them. This is a **requirements note, not the design**: the LLM-assisted
fix-suggestion design this refers to is not in this repository, so where it may say more than this note, it wins
and this note gets reconciled with it before Phase 5 is built.

## The rule

There is exactly **one** data-sharing mechanism. The MCP server, the LLM-assisted fix suggestions and the
privacy promise shown in the AI-assistant view all use it. The promise the user reads is **produced by the
mechanism**, not written next to it in a second, independently worded copy.

## The three tiers

| Tier | What may leave the machine | When |
|---|---|---|
| 1. Aggregate metadata | Counts, flags, verdicts, thresholds and other summary numbers | Default, always |
| 2. Code snippets | Code (for example a suggested fix) | Only after a **separate, explicit opt-in**, and only after the user has seen a **pre-send preview** of exactly what will be sent |
| 3. Raw data values | Nothing | **Never.** Not gated by a setting: there is no path that can carry a data value |

"Architecturally never transmissible" means tier 3 is enforced by construction, not by a switch that could be
turned on. What that implies for Phase 5 (to be confirmed in the spec):

* Every payload that can leave the machine is built from a **closed schema with an allowlist**. No field can
  hold free-form text taken from the data. Anything outside the schema is dropped, not redacted.
* The code that reads the dataset has no route to the outbound path other than through that schema.
* The pre-send preview is rendered **from the same payload object that will be sent**, so it cannot differ.

## One source of truth for the promise

* The tier definitions (what each tier allows, and the user-facing wording for it) live in **one module**.
* The privacy line in the assistant view ("data stayed on this computer, the assistant received a summary
  only") is generated from a **record of what was actually sent** (tier, field names, size), not a fixed
  sentence. If a snippet was sent, the line says so.
* The sidebar's existing line ("Runs on this computer. Your patient data is never uploaded.") describes local
  processing. When Phase 5 adds anything that can send data, that line must come from the same module too.

## Where the API key lives, and where the model runs

* **Bring your own key.** Any credential for a cloud API (tier 2's opt-in code-snippet path) is stored with
  VS Code's `SecretStorage` API, never in `settings.json` and never in any file this extension writes.
  `SecretStorage` is backed by the OS keychain (Windows Credential Manager, Keychain, or libsecret), is
  per-machine, and is never included in a workspace's settings sync or exported config. A key is never logged,
  never put in an error message, and never passed to a tool as a plain argument that could land in a
  process-list snapshot or a log.
* **A local-model path is offered alongside the cloud option, not instead of it.** A local runtime (for
  example Ollama) can serve tiers 1 and 2 without any network call leaving the machine at all -- for a user
  who wants LLM-assisted suggestions but doesn't want a cloud API in the picture regardless of tier. This
  does not relax tier 3: raw data values stay unsent no matter which backend answers, because tier 3's
  guarantee is enforced by the payload schema, not by which model reads the payload.
* Whichever backend is selected, the pre-send preview (tier 2) and the sent-record used to generate the
  privacy line (see above) work identically -- the backend choice changes where an approved payload goes,
  never what is allowed into a payload in the first place.

## The proof (required deliverable of Phase 5)

A test that *proves* the guarantee, not just exercises it:

* Build a synthetic dataset in which every cell holds a unique sentinel value.
* Run every MCP tool at every tier and assert that **no sentinel appears in any output**, including error
  messages and logs.
* Assert structurally that no output type contains a field capable of carrying a data value.

## Also standing for Phase 3 and later

Use the VS Code theme's fonts everywhere, including the setup wizard. Do not bundle a display font for
headings.
