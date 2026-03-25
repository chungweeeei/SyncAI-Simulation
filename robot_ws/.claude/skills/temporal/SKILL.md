---
name : Temporal Python Pro
description: Expert-level guidance and implementation for Temporal workflows using the Python SDK, focusing on best practices for durable execution, error handling, and testing.
---

## Usage Scenarios

### Use This Skill When:
* Developing or debugging **Temporal Python** workflows and activities.
* Requiring architectural guidance on **durable execution** or distributed transactions.
* Implementing best practices for worker configuration and testing.

### Do Not Use This Skill When:
* The task is unrelated to the Temporal Python SDK.
* You are working with Temporal SDKs for other languages (Go, Java, TypeScript) unless comparing patterns.

---

## 🛠 Instructions & Core Principles
1. **Define Boundaries:** Clearly separate Orchestration (Workflows) from Execution (Activities).
2. **Enforce Determinism:** Never allow non-deterministic code (e.g., `datetime.now()`) inside workflow definitions.
3. **Prioritize Safety:** Use proper timeout configurations and idempotency logic for all activities.
4. **Reference Implementation:** For complex templates, refer to `resources/implementation-playbook.md`.

---

## Technical Capabilities

### 1. Workflow Orchestration
* **@workflow.defn:** Implementation of entry points using `@workflow.run`.
* **Deterministic APIs:** Using `workflow.now()`, `workflow.sleep()`, and `workflow.random()`.
* **Advanced Patterns:** Child workflows, signals (`@workflow.signal`), and queries (`@workflow.query`).
* **Versioning:** Handling logic changes with `workflow.get_version()`.

### 2. Activity Execution Models
Temporal Python supports three distinct models to prevent blocking the event loop:

| Model | Implementation | Best For |
| :--- | :--- | :--- |
| **Async** | `asyncio` | API calls, async DB drivers. |
| **Multithreaded** | `ThreadPoolExecutor` | Blocking I/O, synchronous clients. |
| **Multiprocess** | `ProcessPoolExecutor` | CPU-bound tasks, Data Science, ML. |

### 3. Reliability & Error Handling
* **Retry Policies:** Customizing backoff coefficients and non-retryable error types.
* **Timeout Management:** * `ScheduleToClose`: Overall limit.
    * `StartToClose`: Single attempt limit.
    * `Heartbeat`: Liveness detection for long-running tasks.
* **Saga Pattern:** Implementing compensation logic for distributed transactions.

### 4. Testing & QA
* **Time-Skipping:** Using `WorkflowEnvironment` to execute long-running workflows instantly.
* **Mocking:** Injecting mock activities into workflow tests.
* **Replay Testing:** Running production event histories against new code to prevent non-determinism.

---

## Critical Constraints (The "Never" List)
* **NEVER** use `time.sleep()` in a workflow; use `await workflow.sleep()`.
* **NEVER** perform I/O (disk/network) in a workflow; move it to an Activity.
* **NEVER** use global variables that can be modified by workflows.
* **NEVER** ignore `Heartbeat` for activities lasting longer than a few minutes.

---

## Resources
* **Official SDK:** [python.temporal.io](https://python.temporal.io)
* **Core Docs:** [docs.temporal.io](https://docs.temporal.io)
* **Testing:** [docs.temporal.io/develop/python/testing-suite](https://docs.temporal.io/develop/python/testing-suite)

---
**Key Mantra:** *Workflows are for orchestration; Activities are for side effects.*