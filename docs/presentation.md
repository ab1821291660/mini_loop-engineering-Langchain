# Loop Engineering

---
参考：langchain的 https://www.langchain.com/blog/the-art-of-loop-engineering


## Slide 1 — Why Is Everyone Talking About Loop Engineering?

In June 2026, **loop engineering** became a popular term in the AI coding community.

Peter Steinberger said:

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents."

Boris Cherny, the creator and head of Claude Code, described using loops that decide what Claude should do and generate prompts for other Claude instances:

> "I don't prompt Claude anymore. I have loops running. They're the ones prompting Claude and figuring out what to do."

Addy Osmani then published an article titled **"Loop Engineering,"** giving the idea a clearer definition and architecture.

The phrase sounded new.

But was the actual engineering practice new?

---

## Slide 2 — The Principle Existed Before the Buzzword

Loops have always been part of engineering:

```text
Act → observe → evaluate → adjust → repeat
```

We already see this principle in:

* Feedback-control systems
* CI/CD pipelines
* Workflow orchestration
* Automated testing
* AI agents that call tools repeatedly

Andrew Ng called loop engineering a **"hot buzzphrase."** He explained that closing the agentic coding loop had already started taking off near the end of 2025. He also said that during 2025, developers—including himself—were manually testing agent-generated software and asking agents to fix the problems.

So the practice came before the popular name.

---

## Slide 3 — What Does the Current Buzzword Mean?

### It Is Not Just a Simple Agent Loop

An individual coding agent already has an internal loop:

```text
Plan → act → observe → continue
```

That loop helps one agent complete one assignment.

Loop engineering operates at another level:

```text
Coordinator identifies work
        ↓
Coordinator creates an assignment
        ↓
Worker agent runs its internal loop
        ↓
Reviewer evaluates the result
        ↓
Coordinator records the outcome
        ↓
Coordinator selects the next assignment
```

The worker agent's internal loop is part of the system, but it is not the entire meaning of loop engineering.

A useful distinction is:

> **The internal loop controls how an agent works.**
>
> **The external loop controls when agents work, what they work on, and what happens after they finish.**

This external coordination layer is the feature emphasized by Steinberger, Cherny, and Osmani.

Previously, the developer was the loop:

```text
Human selects task
      ↓
Human writes prompt
      ↓
Agent performs work
      ↓
Human checks result
      ↓
Human writes next prompt
```

The new idea is to engineer a system that performs more of this coordination. Addy Osmani describes it as **replacing yourself as the person who repeatedly prompts the agent**:

```text
Human defines objective
      ↓
System finds or selects work
      ↓
System prompts agents
      ↓
Agents perform the work
      ↓
System verifies and records results
      ↓
System decides what happens next
```

---

## Slide 4 — Four Levels of Loops (per LangChain)

LangChain describes four levels of loops, which **nest**: each outer loop controls or improves the loop inside it.

### Level 1 — Agent Loop (the inner loop)

The model repeatedly calls tools until it completes a task.

```text
Receive task → plan action → use a tool → observe result → continue until done
```

For example, a coding agent may read a file, edit the code, run a test, inspect the failure, and make another change. This is the agent's **plan–act–observe loop**.

### Level 2 — Verification Loop

A grader operates outside the agent and checks whether the completed work is acceptable, returning feedback when it fails.

```text
Agent completes task → grader checks result → pass, or return feedback → agent retries
```

The verifier may use automated tests, rules, an evaluator model, or human review.

### Level 3 — Event-Driven Loop

A schedule, webhook, or external event automatically starts the agent, so a human no longer has to begin every run.

```text
New issue, failed test, schedule, or webhook → agent starts → result is checked
```

### Level 4 — Hill-Climbing Loop (the outer improvement loop)

Traces from previous runs are analyzed and used to improve the agent harness itself.

```text
Run harness → collect traces → analyze failures → improve harness → run again
```

The **inner loop** tries to improve the **task result**.
The **outer loop** tries to improve the **agent system that produces the result**.

**Loop engineering is stacking these loops**, not any single one — LangChain's point is
that the value compounds as you add layers. Our demonstration focuses on the outermost
layer, the Level 4 hill-climbing loop (see Slide 6 for it running on real code).

---

## Slide 5 — Harness Engineering vs Loop Engineering

### What Is the Agent Harness?

The harness is the operating environment around an agent. It includes:

* System prompt
* Context and instructions
* Available tools
* Shell and file access
* Permissions
* Memory
* Execution environment
* Graders and tests
* Safety and stopping rules

### Harness Engineering

Harness engineering asks:

> **How should one agent be equipped so it can perform a task reliably?**

It designs the environment in which the inner agent loop operates.

```text
┌─────────────────────────────────┐
│          Agent Harness          │
│                                 │
│  Prompt, tools, context, tests  │
│                                 │
│       ┌─────────────────┐       │
│       │   Agent Loop    │       │
│       │ Plan–Act–Observe│       │
│       └─────────────────┘       │
└─────────────────────────────────┘
```

### Loop Engineering

Loop engineering asks:

> **How should the complete system repeatedly run, evaluate, and improve that harness?**

```text
Run harness
     ↓
Evaluate performance
     ↓
Analyze traces and failures
     ↓
Change prompt, tools, or permissions
     ↓
Run the improved harness again
```

It is called **hill climbing** because every iteration attempts to move toward a
better-performing configuration. The system is not only fixing the software — it is
improving **how the coding agent is instructed, equipped, and evaluated**.

---

## Slide 6 — Slide 4's Level 4, Running on Real Code

Slide 4 defined the hill-climbing loop in the abstract. Here it is instantiated in
this repo — the same loop, but with real files, real knobs, and a real score.

| Abstract step (Slide 4) | Concrete piece in the demo |
|---|---|
| The harness | Deep Agents + `system_prompt` + `enable_shell` |
| The task | 3 bug tickets against the `acme_billing` package |
| Run the harness | agent reads/edits code, tries to fix the bug |
| Collect traces | `data/traces.jsonl` |
| Verify | pytest **+ process checks** (read the test, run pytest, edit right module) |
| Analyze failures → improve harness | `improver.py` rewrites `system_prompt` + `enable_shell` |
| Score | pass rate across the 3 tickets |

### The knob that actually changes

The starter config is **deliberately weak**: `enable_shell = false`, plus a prompt
that forbids reading tests and running pytest. With no shell it *cannot* run pytest,
so verification fails no matter what code it writes.

```text
Iteration 1   enable_shell=false, weak prompt   →  0 / 3   (can't run pytest)
   improver rewrites the harness config ↓
Iteration 2   enable_shell=true,  fixed prompt   →  climbs
Iteration 3   ...                                →  target reached
```

The agent is not just retrying the same task. The **outer loop is editing the harness
itself** between runs — improving *how the agent is instructed, equipped, and
evaluated*. That edit-the-harness step is the whole point of loop engineering.
