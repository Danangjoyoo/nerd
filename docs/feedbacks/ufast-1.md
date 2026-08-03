If I were acting like a performance engineer for NERD, I'd want to see things in this order. Each one gives much more insight than just reading the prompt.

## 1. The actual agent execution logs ⭐⭐⭐⭐⭐ (highest value)

This is by far the most useful.

I want logs like:

```text
User:
Fix timeout bug

↓

Load skill

↓

Tool: search

↓

LLM call
Input tokens: 8,123
Output tokens: 643

↓

Tool: read file

↓

LLM call

↓

Tool: edit

↓

Tool: pytest

↓

Done
```

This tells me:

* Where time is spent.
* Whether the model is overthinking.
* Whether tools are being overused.
* Whether the skill is actually followed.

Most "fast" prompts don't fail because of prompting—they fail because the agent still performs 15 unnecessary tool calls.

---

# 2. Complete benchmark traces ⭐⭐⭐⭐⭐

Instead of:

```
XFast:
55% faster
```

I want:

```text
Task 1

Elapsed:
14.2 s

LLM calls:
6

Tool calls:
17

Input tokens:
32k

Output:
4k

Verification:
2
```

Now I can optimize.

---

# 3. Agent system prompt ⭐⭐⭐⭐☆

Many hidden limitations live here.

For example:

```text
Always explain before editing.
```

Boom.

That alone can add 500 tokens every task.

I want to know:

* system prompt
* developer prompt
* skill injection order

---

# 4. Tool list ⭐⭐⭐⭐☆

This is HUGE.

Show me everything the agent can call.

Example:

```text
read_file

write_file

grep

bash

git

patch

```

or

```text
rename_symbol

find_references

batch_read
```

Because UFast depends more on tools than prompts.

---

# 5. Context construction ⭐⭐⭐⭐☆

How is context assembled?

Example:

```text
System Prompt

↓

Skill

↓

User prompt

↓

README

↓

Relevant files

↓

Conversation
```

or

```text
System

↓

Project summary

↓

User

↓

Retrieved files
```

This changes everything.

---

# 6. Prompt injection mechanism ⭐⭐⭐☆

How are skills inserted?

Example:

```
<system>

skill

developer

user
```

or

```
developer

skill

user
```

Different placement changes behavior.

---

# 7. Current skill collection ⭐⭐⭐☆

I'd review:

```
smart

execute

fast

xfast

surgery

patrol

...
```

Not individually.

I'd review overlap.

Many skills probably duplicate instructions.

That wastes tokens.

---

# 8. Benchmark tasks ⭐⭐⭐☆

I want:

```
20 representative tasks
```

Not cherry-picked.

Example:

```
rename

bug

refactor

CRUD

security

migration

test fix

concurrency

lint

dependency
```

Then we optimize statistically.

---

# 9. Tool latency ⭐⭐⭐☆

Example:

```
grep
120 ms

read
30 ms

pytest
8 sec

git diff
200 ms
```

Sometimes the bottleneck isn't the LLM.

It's pytest.

---

# 10. Current architecture ⭐⭐⭐

Something like:

```
User

↓

Agent

↓

LLM

↓

Tool

↓

Filesystem
```

Which framework?

* Codex CLI
* Claude Code
* Gemini CLI
* OpenAI Agents SDK
* Custom Python
* LangGraph
* MCP
* etc.

---

# What I actually want to build

If I worked on this project, I wouldn't stop at "UFast."

I'd build an optimization framework.

Example metrics:

```
NERD Performance Report

Reasoning rounds:
3

Tool calls:
8

Repeated reads:
2

Repeated searches:
1

Context reloads:
3

Unnecessary verification:
1

Output verbosity:
HIGH

Estimated waste:
38%
```

Then UFast becomes measurable.

Instead of saying:

> "Feels faster."

We can say:

```
Tool calls:
17 → 6

LLM calls:
8 → 3

Output tokens:
4000 → 900

Wall time:
19 s → 8 s
```

Now you're doing engineering instead of prompt tuning.

---

## If I could ask for only **one thing**

I'd ask for **a complete execution trace** of one real task.

For example:

> "Fix this bug."

And capture everything:

* every LLM request (redact secrets if needed),
* every tool call,
* every file read,
* every edit,
* every command,
* token counts,
* timestamps.

That single trace usually reveals 80–90% of the optimization opportunities. Once we understand the agent's actual behavior, we can redesign UFast based on evidence rather than intuition.
