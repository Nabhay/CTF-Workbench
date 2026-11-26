# CTF Workbench: Human-Centric Design Doc

*A workspace for CTFs and cryptic hunts where the human drives and agents assist. Built on opencode as the agent runtime.*

## 1. Vision

Build the equivalent of IDA, Jupyter, and Obsidian for CTFs: one workspace where a player looks at files, runs tools, keeps notes, tracks leads, and can summon a very capable teammate at any moment. A full VS Code editor runs locally in the same workspace, so you can write and debug your own code without waiting on an agent. The workspace is the product. Agents are something you call on from inside it, or that quietly do cheap, safe work in the background.

**Design goals**

- Useful on day one with zero agents: the toolbox, notebook, and board stand alone.
- Agents propose, humans accept. Nothing an agent claims becomes “confirmed” without evidence or a human click.
- Every tool exists once and has two front ends: a UI panel for humans and an MCP tool for agents.
- Everything is reproducible: every command, tool call, and agent answer is logged with its evidence.
- Works for both classic CTFs (rev, pwn, forensics, crypto, web) and cryptic hunts (wordplay, meta-puzzles, image and audio puzzles, OSINT).

**Non-goals (at least initially)**

- A fully autonomous solver that runs a whole competition unattended.
- Scraping third-party sites such as dcode.fr. Reimplement locally instead.
- Replacing your own judgment: the system speeds up grunt work and widens your search, but you decide what is true.

## 2. Design shifts: agent-centric vs human-centric

| Agent-centric | Human-centric (this design) |
| --- | --- |
| Home screen is an agent dashboard | Home screen is the challenge workbench |
| Agents write to the board directly | Agents propose, you accept into the board |
| Tools exist for agents | Tools are a human toolbox first, exposed to agents second |
| Launch, then monitor | Select something, then ask |
| Autonomy defaults high | Defaults to suggest-only |
| Success = flags solved by the agent | Success = time saved and dead ends avoided for the human |

## 3. Users and scenarios

**Solo player in a weekend CTF.** Drops in challenge files, skims auto-triage results, works the one that looks most promising, and delegates the grind (carving a memory dump, brute-forcing a key) to a background agent.

**Small team in a live event.** Several people on one shared board. One person claims a pwn challenge, another works forensics, and a third reads the suggestions inbox and spots that a key from challenge 3 fits challenge 7. A captain approves flag submissions.

**Cryptic hunt.** Puzzles arrive as text, images, audio, and web pages with no API. The workbench holds the puzzle, the thought board links solved answers into the meta-puzzle, and the toolbox covers anagrams, pattern search, and ciphers. Agents propose interpretations and run wordlist searches.

**Learning and post-event review.** The timeline, board, and notebook turn into a writeup. Agents can replay a challenge from scratch to test whether a hint would have been enough.

## 4. System architecture

```
 Browser UI (workbench)
   │  REST + WebSocket (live board, terminal, events)
   ▼
 Control plane (FastAPI or Node)
   ├─ Board service ───────► Postgres/SQLite (+ Yjs doc store for live notes)
   ├─ Job runner ──────────► triage jobs, tool jobs (queue + workers)
   ├─ Agent manager ───────► opencode serve (sessions, prompts, abort, event stream)
   ├─ Context builder        (board + selection + files → agent prompt)
   ├─ Policy engine          (budgets, allowlist, approvals)
   ├─ Platform clients       (CTFd / rCTF / custom, flag submit queue)
   └─ Sandbox manager ─────► Docker (Kali-based image) + VirtualBox
          ▲
          │ same code
   Tool library (Python) ──► UI panels  and  MCP server for agents
```

**Key principles**

1. **One tool library, two front ends.** A function like `pcap.follow_stream(file, stream_id)` is called by the UI panel directly and by agents through an MCP wrapper. What you see is exactly what the agent saw.
2. **The board is the shared source of truth.** Humans edit it directly; agents write only proposals, which sit in an inbox until accepted.
3. **Sessions are scoped.** Each agent session gets a context package (challenge, relevant board items, selected artifact) and a budget, instead of the whole world.
4. **Everything is an event.** Tool calls, agent messages, board edits, and terminal commands are appended to an event log. The UI, replay, writeups, and evals all read from it.

Beside these, each sandbox also runs a local VS Code editor server, reverse-proxied through the control plane and embedded in the workbench (section 5.4), so humans can code in the same workspace the agents use.

## 5. The workbench (UI)

One screen per challenge, with panes you can rearrange and save as layouts.

### 5.1 Panes

- **Challenge header**: title, category, points, description, hints, remote host, status, claim/owner.
- **Files and artifacts browser**: original files plus everything derived (carved files, decoded blobs, extracted keys), each with hash, origin command, and “derived from” links.
- **Viewers**
  - Hex and strings, with selection, highlight, annotate, and entropy graph.
  - Image viewer with channel and bit-plane toggles, LSB view, histogram, zoom and pixel inspector, EXIF.
  - Audio viewer with waveform and spectrogram.
  - Pcap viewer: conversations table, follow stream, protocol filters, exported objects, TLS decryption with a keylog.
  - Memory image browser: process list, network connections, files, command lines, registry hives, dump a process or file.
  - Binary viewer: Ghidra-backed decompiler beside disassembly, function list, xrefs, strings, rename and retype that persist.
- **Notebook**: markdown notes with runnable cells (cipher op, Python, shell, tool call). Outputs persist and link to the board.
- **Toolbox**: direct panels for dcode-style ciphers, encoders and decoders, hash tools, regex and wordlist search, and the “paste anything” analyzer (see section 8).
- **Board**: leads, facts, dead ends, with provenance and evidence links.
- **Thought board**: graph view of facts, artifacts, and challenges with typed edges.
- **Terminal**: yours, in the sandbox. Commands are logged to the event stream. It sits beside the full local VS Code pane (section 5.4).
- **Sidekick**: chat that already knows the challenge, the board, and your current selection.
- **Inbox**: agent suggestions and triage findings, waiting for accept, dismiss, or try.

### 5.2 Global views

- **Dashboard**: challenges by category, points, and status; who is on what; running jobs and agents; budget burn; flags awaiting approval.
- **Cross-challenge view**: shared keys, passwords, themes, usernames, and wordlists, with “this might apply to challenge X” suggestions. Important for hunts where answers and themes repeat.
- **VM panel**: VMs, states, snapshots, one-click restore, screenshot or console view.
- **Timeline and writeup**: chronological story generated from the event log and board, editable.

### 5.3 Interaction model

- **Command palette** (Ctrl+K) for every tool and action.
- **Selection is context**: highlight bytes, a function, a packet stream, or a ciphertext, and a context menu offers “What is this?”, “Decode”, “Explain”, “Find references”, “Add as lead”, “Send to notebook”.
- **Everything linkable**: any item (offset, function, packet, fact) has a stable reference you can paste into notes or the board.
- **Keyboard first**, dark mode, and saved layouts per category (a rev layout versus a forensics layout).

### 5.4 Local VS Code editor pane

The workbench embeds a full VS Code editor that runs locally inside the challenge sandbox, so you can write, debug, and refactor your own solvers and treat agents as optional help. It does not use GitHub Codespaces, vscode.dev, or any Microsoft-hosted service, and challenge files never leave your machine.

**How it is integrated**

- OpenVSCode Server or code-server (both open source) runs inside each challenge container and listens only on localhost.
- The control plane reverse-proxies it (HTTP and WebSocket) behind the workbench login. The UI shows it as a pane you can dock, split, or pop out into its own window.
- It opens the same mounted workspace the terminal and agents use, with the same toolchain: the Python venv with pwntools and z3, gdb, Ghidra scripts, compilers.
- It starts on demand when you open the pane and stops after an idle timeout. Settings and extensions live on a persistent volume.
- Optional: an “Open in desktop VS Code” button for people who prefer their own install, attaching to the container through Dev Containers or Remote-SSH over localhost.

| Option | What it is | Verdict |
| --- | --- | --- |
| OpenVSCode Server or code-server, embedded | VS Code web UI served locally from the sandbox | Default: same environment as the agents, works offline |
| Desktop VS Code attached to the container | Your installed VS Code via Dev Containers or Remote-SSH on localhost | Optional: best performance and your own setup, but outside the workbench UI |
| Monaco editor only | An editor widget with no extensions, debugger, or terminal | Keep for small viewers (diffs, decompiler output), not as the editor |
| Codespaces, vscode.dev, tunnels | Hosted by GitHub or Microsoft | Excluded: not local |

**Extension ecosystem**

- These servers use the Open VSX registry rather than the Microsoft Marketplace, whose terms limit it to Microsoft’s own builds. Some Microsoft extensions (Pylance, the C/C++ and Remote extensions) are therefore unavailable. Substitutes include basedpyright or Pyright, clangd, and a hex editor extension. Verify each extension you depend on is on Open VSX, or bundle a `.vsix` or pick an alternative.
- The sandbox has no open internet egress, so pre-install extensions as `.vsix` files baked into the image. Disable marketplace access and telemetry.

**CTF Workbench companion extension**

A small extension we write, running inside the editor, ties it to the rest of the workbench:

- **Sidebar views**: Board (leads, facts, dead ends), Artifacts, and the Inbox, with accept, dismiss, and try buttons.
- **Selection commands**: add as lead, run in the toolbox (decode, XOR, hash identify, the paste-anything analyzer), attach a file and line range as evidence, ask the sidekick about the selection.
- **Inline marks**: CodeLens or gutter markers where a line links to a board item or artifact.
- **Virtual documents**: Ghidra decompiler output and disassembly for a function open as read-only editors, with a command that sends a rename back to the Ghidra project.
- **Templates and snippets**: a pwntools skeleton with a local and remote switch, RSA and z3 solver skeletons, Ghidra script and Volatility plugin scaffolds, and a `solve.py` per challenge.
- **Run and debug tasks**: launch configurations for local and remote pwn with transcript logging, gdb attach, and “run in sandbox” buttons. Output goes to the event log.
- **Flag candidates**: a command that proposes a flag to the approvals queue and never submits directly.
- Before building the channel to the sidekick, check whether opencode’s own editor integration can be reused.

**Humans and agents share one workspace**

- **One filesystem**: everything lives under `/work/<challenge>`, a git repo initialized automatically, with automatic checkpoint commits so any change by anyone can be reverted.
- **Agent edits arrive as diffs**: in suggest-only mode agents can read your files and write to a scratch folder. Changes to your code appear in the Source Control view as a proposed patch you accept or reject per hunk. Direct writes to the main workspace are allowed only at autonomy level 3, on a branch or worktree named for the session.
- **Agents see what you do**: saves, the active file, and your selection are published to the control plane (you can switch this off), so the sidekick’s context includes what you have open and the event log records your edits.
- **No clobbering**: an “agent is working on this file” marker and soft locks. If you edit a file an agent is using, the agent is told and continues from your version.
- **Hand-offs both ways**: “Finish this solver” sends the file and selection to a delegated task. “Explain this patch” opens an agent diff with commentary.
- **Inline completions** are off by default. If you want them, they come from a separate completion extension, not from opencode sessions.

**Security and multi-user**

- The editor gives code execution inside the sandbox, which is the point, so: bind to localhost, authenticate through the control plane, mount no credentials, apply the sandbox network allowlist to the extension host and terminals, disable telemetry and settings sync, and keep an extension allowlist.
- Each person gets their own editor session and user-data directory on the shared workspace. Simultaneous co-editing of one file is out of scope for v1; use branches or the shared notebook instead.

**Rollout**

- M1: the bare embedded editor next to the terminal, on the shared workspace, with no extension yet.
- M3: the companion extension with the board sidebar and selection-to-sidekick.
- M5: agent patches as proposed diffs and per-session branches.

## 6. How agents help

Six modes, from least to most autonomous.

1. **Select and ask.** Highlight something and ask about it. The answer appears inline with the exact commands run and their output. Scope is tiny, so it is fast and cheap.
2. **Auto-triage on file drop.** Background jobs (not necessarily LLMs) run on every new file: `file`, `strings`, `binwalk`, `exiftool`, entropy, magic carving, a pcap summary, a quick Ghidra analysis pass, a Volatility `imageinfo` equivalent. Results post as findings. An optional small LLM pass summarizes them into “here is what I would look at first.”
3. **Suggestions inbox.** Watcher agents notice patterns and leave cards: “this blob looks like base64 of gzip”, “this string matches the flag format when ROT13’d”, “this key from challenge 3 decrypts this file”. Each card has accept (becomes a lead), dismiss, or try (runs a sandboxed check and attaches evidence).
4. **Delegated tasks.** Scoped, budgeted jobs you hand off: “decompile and rename everything”, “carve all files from this dump”, “brute-force with these wordlists”, “write a solver once I confirm the algorithm”. Returns a report with artifacts and evidence.
5. **Second opinion.** “Review my board and tell me what I am missing”, “argue against my current theory”, “what would a setter do with this hint?”
6. **Terminal watcher (optional).** The agent sees your terminal and proposes the next command or flags an error. It never runs anything unless you accept.

**Autonomy levels** (per challenge, default is level 1):

| Level | Behavior |
| --- | --- |
| 0 | Agents off. Pure workbench. |
| 1 | Suggest only. Agents answer when asked and post suggestions. |
| 2 | Safe jobs run automatically (triage, read-only analysis). Anything that executes unknown binaries or touches the network asks first. |
| 3 | Delegated tasks may run freely inside the sandbox within budget. Flags and VM changes still need approval. |

## 7. Trust and provenance

The main failure of agent-assisted CTF work is a confident wrong claim that gets copied into notes and then drives hours of wasted effort. The design counters this directly.

- Every item has an **author**: human, tool, or agent.
- Every claim has a **status**: `hypothesis`, `verified`, `confirmed`, `dead_end`.
  - Agent claims start as `hypothesis`.
  - `verified` means a tool reproduced the evidence (a decode really produced printable output matching the flag format, a hash really matched, a key really decrypted the file). The system can promote automatically when a re-runnable check passes.
  - `confirmed` means a human accepted it.
- Every claim links to **evidence**: command, input artifact hashes, output, tool version, timestamp. “Re-run” is one click.
- **Flag candidates** are special: a regex check against the event’s flag format, and a human approval before submission.
- **Dead ends are first-class.** A veto records what was tried and why it failed, and agents receive dead ends in their context so they do not repeat them.
- **Agents cite, not assert.** Answers must reference artifact IDs, offsets, or command outputs. Uncited claims render visibly as unsupported.

## 8. Tool library

Implemented once as a Python package with typed functions and JSON schemas, exposed to the UI via the control plane and to agents via an MCP server.

| Domain | Tools |
| --- | --- |
| General | file, strings, xxd and hex ops, entropy, magic carving, hashing, diff of binaries |
| Reversing | Ghidra headless (decompile, xrefs, strings, rename and retype persistence), radare2 or rizin, angr, objdump, ltrace, strace, gdb scripting, Frida for dynamic work |
| Pwn | pwntools, ROPgadget, one\_gadget, checksec, cyclic patterns, remote connection wrapper with transcript logging, libc database lookup |
| Network | tshark or pyshark (conversations, follow stream, object export, DNS, HTTP, USB HID decoding), TLS decryption via keylog, protocol dissector helpers |
| Memory | Volatility 3 (pslist, cmdline, netscan, filescan, dumpfiles, hashdump, registry, malfind), strings-over-dump search |
| Disk and files | binwalk, foremost or scalpel, Sleuth Kit, mount and browse images, archive and document unpackers (zip, office, PDF object extraction) |
| Stego | zsteg, steghide, stegseek, bit-plane and channel ops, spectrograms, audio DTMF and Morse decoding |
| Crypto | RsaCtfTool-style attacks, SageMath, z3, hashcat and john, XOR key recovery, frequency and IoC analysis, padding oracle helpers |
| Cryptic and wordplay | anagram solver, regex over wordlists (nutrimatic-style), crossword and pattern fill, hidden word and acrostic finders, letter-extraction ops, cipher identification |
| Web and OSINT | Playwright headless browser, ffuf, sqlmap, reverse image search helpers, Wayback lookup, EXIF and geolocation helpers |
| Utility | wordlist manager, shared known-keys table, scratch Python runner, notebook cell executor |

### dcode.fr-style coverage

There is no official dcode API and scraping is fragile, so rebuild the common functionality locally. That gives offline, deterministic, bulk-callable tools for agents.

- **Classical ciphers**: Caesar, ROT-N, Atbash, Affine, Vigenère (with Kasiski and IoC key-length detection), Beaufort, Autokey, Playfair, Two-Square, Four-Square, Bifid, Trifid, ADFGX/ADFGVX, Hill, Rail Fence, Scytale, columnar and double transposition, Polybius, Nihilist, Bacon, Book cipher helpers.
- **Encodings**: Base16/32/58/64/85/91, URL, HTML entities, Morse, Braille, NATO, semaphore, tap code, binary/octal/decimal, A1Z26, Brainfuck and other esolangs, Malbolge, Ook.
- **Hashes and analysis**: hash type identifier, hash lookup against wordlists, n-gram and frequency analysis, IoC, chi-squared scoring, language detection.
- **Number and text utilities**: modular arithmetic, CRT, prime factorization, GCD and modular inverse, base conversion, string transformations (reverse, interleave, every-Nth letter).
- **Fallback**: CyberChef via its Node API for the long tail, and a “recipe” builder in the UI that chains ops.

### “Paste anything” analyzer

The single most useful universal tool: paste text, hex, or an uploaded blob and get a **ranked list of guesses**. It tries encodings, decompressions, single-byte XOR, common ciphers with scoring, hash identification, file magic, and flag-format regex, shows the top candidates with confidence, and lets you chain onward. The same code backs the agent’s “try to decode” action.

## 9. Data model

Core tables (Postgres, or SQLite for the local-first version):

- **events**: id, ts, challenge\_id, actor (human/tool/agent + id), type, payload. Append-only log.
- **challenges**: id, source, category, points, title, description, hints, remote host, status, owner, parent\_meta\_id (for hunts).
- **artifacts**: id, challenge\_id, path, sha256, kind, origin (command or event id), parent\_artifact\_id.
- **items** (leads, facts, dead ends): id, challenge\_id, text, status, author, confidence, pinned, created\_by\_event.
- **evidence**: id, item\_id, artifact\_id, offset range, command, output excerpt, rerunnable (bool).
- **links**: from, to, type (`derived_from`, `unlocks`, `contradicts`, `same_key_as`, `feeds_meta`). Backs the thought board.
- **keys and secrets**: value, kind (password, key, username, theme word), where found, where it worked, where it failed.
- **jobs and sessions**: id, kind, scope, budget, spent, state, opencode session id, report artifact.
- **flags**: candidate, challenge, regex\_ok, approved\_by, submitted\_at, result.
- **notes**: Yjs documents for the notebook, synced live.

## 10. Opencode integration

Opencode is the agent runtime. The control plane never reimplements the agent loop; it prepares context and enforces limits.

- **Server mode**: run `opencode serve` and drive it through the SDK (create session, send prompt, abort, stream events). Verify endpoints against current docs, since the API is still changing.
- **Agent definitions** live in `.opencode/agent/` as markdown with frontmatter: `triage`, `rev`, `forensics`, `crypto`, `cryptic`, `web-osint`, `reviewer`. Each has a short, focused prompt and a restricted tool set.
- **`AGENTS.md`** holds global rules: authorized-CTF scope statement, how to use the board tools, how to cite evidence, never to write directly to confirmed status, how to report.
- **MCP server** (`ctfmcp`) exposes the tool library plus board tools: `board_propose_lead`, `board_attach_evidence`, `board_list`, `artifact_get`, `notebook_append`, `flag_candidate_propose`.
- **Context builder**: for each request, assembles challenge info, the selection, relevant confirmed facts, active leads, and dead ends, keeping the prompt small. Large artifacts are passed by reference with tools to read slices.
- **Event bridge**: opencode’s event stream is translated into UI events (tool call cards, streamed text) and persisted in the event log.
- **Budgeting**: token and wall-clock limits enforced by the control plane, which aborts sessions that overrun and posts a report of what was done.
- **Fork and rewind**: implement on top of stored session history and the event log if the SDK does not provide them directly.

**Shared workspace.** Opencode sessions run in the same sandbox workspace the VS Code pane edits. By default they write only to a scratch folder and return patches for you to accept, and the context builder includes the file and selection you have open (section 5.4).

## 11. Sandbox and VM layer

- **Docker sandbox per challenge**: Kali-based image with the toolchain preinstalled, a mounted workspace, resource limits, and no privileged mode. Agent bash and your terminal both run here. Full permissions inside it are acceptable because it is disposable.
- **Network policy**: default egress is only the declared challenge hosts (allowlist enforced with a proxy or firewall rules). Anything else raises an approval. This is the main guard against an agent wandering onto out-of-scope infrastructure.
- **VirtualBox wrapper** around `VBoxManage`: list, start, stop, snapshot, restore, `guestcontrol run`, file copy in and out, screenshot. Rule: snapshot before any agent action on a VM, and restore is one click.
- **Detonation and suspect binaries**: run in an isolated VM or container with no network, never on the host.
- **Reproducibility**: container images are versioned, so a run can be replayed with the same tool versions.

## 12. Cryptic hunt specifics

Cryptic hunts differ from CTFs: less automation-friendly, more lateral thinking, heavier on text and images, and answers chain into metas.

- **Puzzle ingest**: paste text, upload images, and capture a web page (full-page screenshot plus saved HTML). No platform API is assumed.
- **Thought board** as a first-class tool: nodes for puzzles, answers, and clues, edges for “feeds meta”, with a visible tally of which meta slots are filled and which letters or words are still missing.
- **Theme tracker**: recurring words, names, formats, and cultural references across puzzles, because hunts reuse them.
- **Wordplay tools**: anagram, hidden word, regex over wordlists, letter-position extraction, acrostics, homophones, crossword fill, and nutrimatic-style pattern queries.
- **Vision assist**: agents describe and OCR images, spot patterns (grids, nonograms, ciphers drawn as symbols), and suggest interpretations as hypotheses.
- **Answer validation**: since many hunts reject answers on a rate limit, keep an answer queue with approvals and an attempt log.
- **Brainstorm mode**: an agent generates many candidate interpretations quickly, and you triage them. This is where wide search helps most.

## 13. Platform integration

- **CTFd and rCTF clients**: pull challenges, download files, start instances, read solve state, and submit flags.
- **Flag submission queue**: regex check against the flag format, then human approval, then rate-limited submit, with the response logged. Prevents lockouts and accidental wrong submissions.
- **Generic importer**: manual entry or JSON import for events without an API.
- **Notifications**: Discord or Slack hooks for solves, approvals waiting, and agent reports.

## 14. Collaboration

Optional for the first version, but the data model should allow it.

- Shared notebook and board using Yjs for conflict-free live edits.
- Presence, challenge claiming, and comments on items.
- Roles: viewer, operator, and admin (flag approval, policy changes, VM control).
- Per-person agent budgets, so one player cannot burn the team’s allowance.
- Everyone sees the same inbox, with a “taken by” marker to avoid duplicate work.

## 15. Safety, scope, and rules

- **Check the event’s rules.** Many CTFs restrict or ban AI assistance, or limit it to certain forms. Add a per-event “rules” field and an assistance policy that disables disallowed modes (for example, no auto-solving, or no external model calls).
- **Scope statement** in `AGENTS.md` and the context builder: this is an authorized CTF, the in-scope hosts and files are listed. This also removes needless refusals.
- **Allowlist enforcement** is technical (proxy and firewall), not just a prompt instruction.
- **Secrets**: platform tokens and credentials are held by the control plane and injected only into the tools that need them, never placed in prompts.
- **Access control**: the workbench gives code execution in a sandbox, so require authentication, bind to localhost or a VPN, and log all actions.
- **Data handling**: challenge files may include malware samples. Keep them inside the sandbox and clearly labeled.

## 16. Suggested stack

| Layer | Choice |
| --- | --- |
| Frontend | React or Svelte, Tailwind, React Flow or Cytoscape (graph), Monaco (code and decompiler), xterm.js (terminal), a hex viewer component, wavesurfer.js (audio) |
| Live collaboration | Yjs with a websocket provider |
| Control plane | FastAPI (Python, so the tool library is shared) with a worker queue (Celery, RQ, or arq) |
| Storage | SQLite for local-first, Postgres for teams; artifacts on local disk or S3-compatible store |
| Agent runtime | opencode server plus SDK |
| Tool exposure | Python tool library, MCP server wrapper |
| Sandbox | Docker, VirtualBox via VBoxManage |
| Search over past writeups | embeddings in SQLite or pgvector over CTFtime and your own writeups |
| Editor | OpenVSCode Server or code-server inside each sandbox, extensions from Open VSX baked into the image, plus our companion extension; Monaco only for small viewers |

## 17. Roadmap

Each milestone should be usable by itself.

**M1: Workbench core, no agents** Board and notebook with provenance fields, file import, hex and strings viewer, the cipher and encoding toolbox, the paste-anything analyzer, a sandbox terminal, and the embedded local VS Code pane. Exit criterion: you can solve a simple crypto and a simple forensics challenge entirely by hand faster than with loose terminals.

**M2: Auto-triage and viewers** Background job runner, triage on file drop, pcap viewer, image and stego viewer, memory image browser. Findings post to the inbox.

**M3: Sidekick** Control plane to opencode, the context builder, the MCP tool server, select-and-ask, and streamed answers with evidence cards. Proposals flow into the board as hypotheses.

**M4: Suggestions and verification** Watcher agents, the inbox with accept, dismiss, and try, and automatic promotion to `verified` through re-runnable checks.

**M5: Delegated tasks** Scoped jobs with budgets, Ghidra headless integration with persistent renames, Volatility workflows, reports as artifacts, and the autonomy dial.

**M6: Hunts and platforms** Thought board, theme tracker, cryptic tools, CTFd and rCTF sync, and the flag and answer queue with approvals.

**M7: VMs and team features** VirtualBox panel with snapshots, Yjs collaboration, roles, notifications.

**M8: Writeups, retrieval, evals** Timeline-to-writeup generation, retrieval over past writeups, and the evaluation harness (next section).

## 18. Evaluation

Treat this like a product with measurable quality, not a demo.

- **Benchmarks**: replay archived CTF challenges (picoCTF, past CTFtime events, Cybench-style tasks) with the agents at each autonomy level.
- **Metrics**: time to first useful finding, percent of triage findings you accepted, false-claim rate (agent hypotheses later refuted), tokens per solve, solves per hour with and without the sidekick.
- **Replay**: because every action is logged, a past session can be re-run against new prompts or models to compare.
- **Regression set**: a small fixed set of challenges per category that every prompt or tool change must still solve.
- **Human study**: during real events, record when you reached for an agent and whether it helped. That tells you which features to invest in.

## 19. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Agents assert wrong things that spread | Provenance, `hypothesis` default, mandatory evidence, auto-verification by re-run |
| Scope creep into building an IDA clone | Wrap Ghidra and existing viewers; build only the glue and the board |
| Ghidra headless is slow and fiddly | Cache analysis projects, run triage passes in the background, expose results incrementally |
| Token and cost blowups | Budgets per session and per challenge, small scoped contexts, cheap models for triage |
| Out-of-scope network activity | Technical allowlist and approvals, not prompt rules alone |
| Event rules ban AI help | Per-event policy that disables modes, visible in the UI |
| Opencode API changes | Thin adapter layer around the SDK so only one module changes |
| Real-time collaboration complexity | Design data model for it, build it late, use Yjs rather than custom sync |
| Embedded editor widens the attack surface and drifts from what agents see | Localhost bind behind the control plane proxy, extension allowlist, one shared git workspace with checkpoints, agent changes arrive as diffs |

## 20. Open questions

1. **Solo or team?** This decides whether to start with a local-first app (SQLite, no auth) or build live collaboration in from the start.
2. **Which events are you targeting?** Classic jeopardy CTFs, attack-defense, or cryptic hunts determine which viewers and tools come first.
3. **Which models?** Whether you want to mix a strong model for delegated tasks with a cheap one for triage and suggestions.
4. **Local or hosted?** Running everything on your machine is simplest, but a team may want a shared server.
5. **Rules compliance:** which of your target events allow AI assistance, and in what form?

## 21. First concrete steps

1. Define the SQLite schema for events, items, artifacts, and links.
2. Scaffold the Python tool library with five tools (strings, hex, base-N decode, Caesar and Vigenère, hash identify) and the paste-anything analyzer.
3. Stand up FastAPI with a board API and a minimal React UI: file list, hex viewer, board, notebook, embedded code-server pane.
4. Add the MCP wrapper so the same tools are callable from opencode.
5. Wire one sidekick flow: select text, ask “what is this?”, get an answer with evidence, accept it as a lead.

That sequence yields something you can use in the next CTF while the heavier pieces (Ghidra, VMs, delegated agents) are built behind it.
