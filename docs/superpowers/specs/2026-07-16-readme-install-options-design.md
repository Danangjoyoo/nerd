# README Agent Install Options Design

## Goal

Make the README installation instructions easier to scan and copy by presenting one valid multiline command for each supported agent: Codex, Claude Code, and Cursor.

## Approved Presentation

The existing `## Install` section will retain a single Bash code block. Inside it, each supported agent will have a short comment label followed by the same multiline command structure:

```bash
# Codex
npx skills add danangjoyoo/nerd \
  --global \
  --agent codex \
  --skill '*' \
  --yes
```

The block will repeat this structure for `claude-code` and `cursor`, labeled `# Claude Code` and `# Cursor`. Each command must be independently copyable and executable.

## Command Semantics

- `npx skills add danangjoyoo/nerd` selects the canonical public repository.
- `--global` installs into the user's global agent skill directory.
- `--agent <agent>` targets exactly one selected client.
- `--skill '*'` installs all five public Nerd skills.
- `--yes` makes installation non-interactive.

Literal pipe characters will not be used as agent separators because shells interpret them as pipelines. A repeated `--agent` all-agent command is also excluded because the approved experience is an explicit user choice.

## Files and Responsibilities

- `README.md` owns the visible agent labels and multiline installation commands.
- `tests/test_readme.py` owns the public installation contract and will verify the normalized command for all three supported agents, the three labels, and the absence of the invalid piped-agent form.

## Testing Strategy

Implementation will use a test-first cycle:

1. Update the README contract test to require the new multiline presentation and reject the piped-agent form.
2. Run the focused test and confirm it fails because the README still contains one-line commands.
3. Replace only the current installation code block with the approved multiline commands.
4. Run the focused README test, all README tests, and the full repository suite.
5. Verify the final diff contains no unrelated README changes.

## Non-goals

- Do not change the repository slug, supported agent set, install scope, selected skill set, or confirmation behavior.
- Do not remove or change the existing helper-script instruction.
- Do not change the README header, banner, badges, benchmarks, or skill descriptions.
- Do not add a command that installs into all agents simultaneously.
