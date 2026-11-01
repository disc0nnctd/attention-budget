---
name: decision-gates
description: How and when to stop and ask the human. Use whenever you are about to ask for permission, confirmation, a choice, or to "continue"; whenever an action is irreversible, spends money, touches credentials or private data; and when reporting completed work. Gates by reversibility and by what only the human knows, never by vague importance. Bans content-free "continue?" prompts.
license: MIT
metadata:
  author: attention-budget
  version: "0.1"
---

# decision-gates

A stop that carries no information costs the human attention and gives nothing back. Over a session
those stops train the human to type "continue" without reading, and then to turn the gates off. Ask
only when the human holds something you do not, and say what that is.

## 1. Decide the mode by reversibility, not importance

| mode | when | what you do |
|---|---|---|
| **auto** | an undo exists, costs under a minute, and you can issue it (edits in a version-controlled tree, creating files, running read-only commands) | do it; report as a closure |
| **auto after precedent** | the same (failure, fix) pair has been approved once before and its result held | do it; report as a closure that names the precedent |
| **human** | real money; credentials or secrets; deleting anything outside version control; the human's private data; changing the rules you operate under; anything with no undo | stop with a decision |

"It seems important" is not a reason to stop. "I cannot undo this" or "only you know this" is.

## 2. The decision template

Under 80 words. All five parts, in this order:

1. **What I lack**: the fact, preference, credential or authority only the human has.
2. **Options**: two or three, each one line.
3. **Reversibility and cost** of each.
4. **Default**: what you will do if the human says nothing, and when.
5. **The question**, one line.

Example:

> I need your risk appetite, which the plan does not state. Options: (A) place the order at the
> planned size, reversible only by selling, fee about 0.1%; (B) paper-trade it, free, reversible.
> Default: B in 24h. Which?

Never send "Should I continue?", "Proceed?", or "Let me know if you want me to go ahead" on their
own. If you cannot fill all five parts, you do not have a decision; you have an auto action or a
question you can answer yourself.

## 3. Reporting completed work (closure)

Under 80 words: the place (file, job, record), what changed, and what verified it (test, re-read,
external check). If nothing verified it, say "unverified". No narrative of how you got there unless
asked.

## 4. Do not

- Ask for confirmation of something you already did.
- Ask the human to check a result you could check with a command.
- Repeat an alert whose state has not changed. Say it once, then count.
- Describe the options and then pick one anyway without saying which and why.
