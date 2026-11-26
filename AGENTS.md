# Agent instructions

This repository is the working journal for
[Reussir](https://github.com/reussir-lang/reussir). It is a
[Forester](https://www.forester-notes.org/) forest: many small notes ("trees")
with permanent addresses that link to and include each other. Design notes,
decisions, open problems, examples, motivations and dated changelog entries
for Reussir are written here, not in the Reussir repository.

Write here freely as part of your work. You do not need to ask first.

## Tools

Everything comes from the flake. Do not rely on tools installed on the host.

```sh
nix develop                 # shell with forester, jj, git, python3, rg
journal-new <kind>          # allocate an address and create the tree file
journal-build               # forester build forest.toml
journal-serve               # build, then serve at http://localhost:1313/reussir-agentic-journal/
nix flake check             # the build must pass with no diagnostics
```

Outside the shell the same commands are `nix run .#new -- <kind>`,
`nix run .#build` and `nix run .#serve`.

## Kinds of trees

| Kind | `journal-new` argument | Address | Directory | `\taxon` |
|---|---|---|---|---|
| Design note | `design` | `design-XXXX` or `design-<slug>` | `trees/design/` | `Design` |
| Decision | `decision` | `dec-XXXX` | `trees/decision/` | `Decision` |
| Open problem | `problem` | `prob-XXXX` | `trees/problem/` | `Problem` |
| Changelog entry | `log` | `log-XXXX` | `trees/log/` | `Change` |
| Example | `example` | `ex-XXXX` | `trees/example/` | `Example` |
| Motivation | `motivation` | `mot-XXXX` | `trees/motivation/` | `Motivation` |
| Insight | `insight` | `ins-XXXX` | `trees/insight/` | `Insight` or `Hypothesis` |
| Session | `session` | `ses-XXXX` | `trees/session/` | `Session` |
| Identity | (by hand) | `claude-fable-5-2`, ... | `trees/people/` | `Person` |

- Addresses are global and permanent. Directories are only for tidiness; they
  are not part of the address. Never rename an address: code and other trees
  point at it.
- A design note may use a readable address (`design-<slug>`) when code will
  cite it. Everything else uses the random address `journal-new` allocates.
- Keep a tree to one idea. Put an example, a motivating case or an unresolved
  question in its own tree and `\transclude` it from every note it belongs to,
  rather than growing one long document.
- The hub trees (`designs`, `decisions`, `open-problems`, `examples`,
  `insights`, `sessions`) list trees by taxon with a query, so a new tree with
  the right `\taxon` shows up without further edits. Two hubs are maintained
  by hand: add a new design note to `trees/designs.tree`, and see
  "Changelog entries" below.

## Frontmatter

Every tree starts with:

```
\title{Short title, sentence case}
\taxon{Design}
\date{2026-11-13}
\author{claude-fable-5-2}
\contributor{schrodingerzy}
\tag{...}
\import{base-macros}
```

- `\date` is the creation date. When you substantially revise a tree, do not
  change it; set `\meta{updated}{YYYY-MM-DD}`.
- Design notes, decisions and problems also carry `\meta{status}{...}`,
  `\meta{created}{...}` and, once finished, `\meta{completed}{...}`, and repeat
  the status as the first paragraph (`\p{\strong{Status:} open.}`) so that it
  is visible on the page. Statuses: `draft`, `accepted`, `implemented`,
  `superseded`, `open`, `closed`.
- Changelog entries carry `\tag{changelog}`, one area tag (`language`,
  `stdlib`, `compiler-runtime`, `tooling`, `platforms`), a release tag
  (`unreleased` or `v0.1.0`) and `\meta{pr}{NNN}`.

## Identity

- `\author` is the agent that wrote the tree: the identity tree of your exact
  model version, for example `claude-fable-5-2`. `\contributor` is the person
  who directed the session, and any agent or person who later revised the
  tree. Both take the address of a tree in `trees/people/`.
- If your model version has no identity tree yet, create one by copying an
  existing agent tree, and add it to `trees/agents.tree`. Do not write under
  another version's identity.
- Each working session leaves one session tree (`journal-new session`): date,
  `\meta{harness}{...}`, `\meta{model-id}{...}`, the Reussir branch or pull
  request, and links to the trees it created or changed.
- When you revise a tree written by someone else, add yourself as
  `\contributor`; do not replace the `\author`.

## Changelog entries

One tree per change, written when the change is made, with the date it was
made. Then add it by hand in two places, newest first:

1. the month tree `trees/log/log-YYYY-MM.tree` (create it, and add it at the
   top of `trees/changelog.tree`, if the month is new);
2. the release tree `trees/log/release-unreleased.tree`, under its area.

Link the entry to the design note, decision or problem it relates to.

## Insights

Record a lesson only if it would help a later session avoid the same dead end
or reach the fix faster. Keep it to a few sentences and name its source (pull
request, issue or session tree). Use `\taxon{Hypothesis}` if it was not
verified, and change it to `\taxon{Insight}` once it is.

## Writing rules

- Write new and changed trees in ASD-STE100 Simplified Technical English:
  approved words with their approved meanings, sentences of at most 20 words
  for an instruction and 25 for a description, the active voice, and one
  instruction in each sentence. Technical names, such as code identifiers,
  stay as they are.
- Write for a reader who has no access to any conversation. Trees may cite
  pull requests (`\pr{123}`), issues (`\issue{123}`) and session trees. They
  must never refer to a chat or to "the user".
- Record lasting instructions from a maintainer in
  `trees/policy/standing-policies.tree` in the same session, with the date.
  Read that tree and `trees/policy/accepted-risks.tree` before reviewing or
  restructuring the journal; do not re-raise an accepted risk.
- Do not delete a decision or a closed problem. Mark it superseded or closed
  and link what replaced it.

## Markup

Forester markup looks like LaTeX with markdown links. The pitfalls:

- Every paragraph must be wrapped: `\p{...}`. Bare text is not a paragraph.
- Do not hard-wrap prose. One paragraph is one line.
- `%` starts a comment that swallows the rest of the line. Write `\%`.
- `{ } [ ] \ #` are syntax. In prose, put them in inline code or a verbatim
  span. Parentheses must be balanced within a paragraph.
- Inline code: `\code{\verb~|Tensor<bool>~}`. The verbatim span is
  `\verb<mark>|...<mark>`, where `<mark>` is any text that does not occur in
  the content (`~` usually works; use `!!` when the content has a `~`).
- Code block:

  ```
  \pre{\verb~|
  fn main() {}
  ~}
  ```

- Links: `[text](address)` for a tree. For a URL use
  `\<html:a>[href]{\verb~|https://example.org/x#y~}{text}`.
- Lists: `\ul{\li{...}\li{...}}`, `\ol{...}`. Emphasis: `\em{}`, `\strong{}`.
- Tables: `\table{\tr{\th{A}\th{B}}\tr{\td{1}\td{2}}}` (from `base-macros`).
- Include another tree as a section: `\transclude{address}`. Declare a section
  with its own address inline: `\subtree[address]{\title{...} ...}`.
- A markdown draft can be converted with
  `python3 scripts/md2tree.py draft.md <address>`.

## The marker in Reussir source

Reussir code cites a tree as `*agentic-note*: <address>`. To resolve one,
search here: `rg -F '<address>' trees/`. A whole tree is the file of that
name; a section is declared as `\subtree[<address>]`. If you give a tree or
section an address that code will cite, that address is permanent.

## Version control

The repository is a git repository managed with jujutsu (`jj`), colocated.
Use `jj` from the flake shell.

- Start a session with `jj new` on top of `main` and describe it with
  `jj describe -m "[scope] description"`, for example
  `[design] note on borrowed counted arguments`.
- Use the scope of the kind of tree you touched: `design`, `decision`,
  `problem`, `log`, `insight`, `session`, `people`, `policy`, `infra`.
- When several agents work at once, give each its own working copy with
  `jj workspace add ../journal-<name>`.
- Do not create git submodules. Do not push unless asked.
- Before finishing, run `nix flake check` (or `journal-build`) and fix every
  diagnostic.
