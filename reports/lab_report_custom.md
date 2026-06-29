# Day 08 Lab Report — LangGraph Agentic Orchestration

## 1. Team / Student
- **Name**: Vu Tuan Hoang
- **Date**: 2026-06-29
- **Summary**: Completed 8 scenarios with a success rate of 100.00%.

## 2. Architecture
The production support-ticket agent workflow uses a structured LangGraph `StateGraph` designed with conditional routing, HITL gates, and bounded retry loops:
- **Intake & Classify**: Normalizes query and uses DeepSeek/OpenAI LLM with structured output (`with_structured_output`) to classify queries into 5 intent priority levels (`risky` > `tool` > `missing_info` > `error` > `simple`).
- **Tool Execution & Retry Loop**: Executes tool queries. If errors occur or evaluation fails (`evaluate_node`), routes to `retry_or_fallback_node` up to `max_attempts` before escalating to `dead_letter_node`.
- **HITL Approval**: High-risk actions route to `risky_action_node` and `approval_node` for verification before proceeding to tools.
- **Finalization**: All execution paths guarantee termination at `finalize_node` before reaching `END`.

## 3. State Schema
The `AgentState` schema balances lean serialization with auditability:

| Field | Reducer | Why |
|---|---|---|
| `messages` | append (`add`) | Audit conversation history and event tracking |
| `tool_results` | append (`add`) | Preserve sequence of tool outputs and retry attempts |
| `errors` | append (`add`) | Log transient tool errors and retry failures |
| `events` | append (`add`) | Full structured observability log for grading |
| `route` | overwrite | Tracks current classified intent route |
| `evaluation_result` | overwrite | Drives retry loop conditional gating |
| `proposed_action` | overwrite | Holds pending action payload for HITL approval |
| `approval` | overwrite | Records decision and metadata from reviewer |

## 4. Scenario Results
- **Total Scenarios**: 8
- **Success Rate**: 100.00%
- **Total Retries**: 0
- **Total Interrupts**: 2
- **Avg Nodes Visited**: 11.50

| Scenario | Expected Route | Actual Route | Success | Retries | Interrupts |
|---|---|---|:---:|:---:|:---:|
| `C01_greeting` | `simple` | `simple` | ✅ | 0 | 0 |
| `C02_billing_faq` | `simple` | `simple` | ✅ | 0 | 0 |
| `C03_check_shipment` | `tool` | `tool` | ✅ | 0 | 0 |
| `C04_verify_subscription` | `tool` | `tool` | ✅ | 0 | 0 |
| `C05_ambiguous` | `missing_info` | `missing_info` | ✅ | 0 | 0 |
| `C06_cancel_sub` | `risky` | `risky` | ✅ | 0 | 2 |
| `C07_database_timeout` | `error` | `error` | ✅ | 0 | 0 |
| `C08_api_crash` | `error` | `error` | ✅ | 0 | 0 |

## 5. Failure Analysis
1. **Transient Tool Failures & Bounded Retries**: When tool lookups timeout or fail (e.g. `S05_error`), the graph captures the error in state and routes through `evaluate_node` to `retry_or_fallback_node`. Bounding retries via `attempt < max_attempts` ensures the system self-heals without infinite looping. If retries are exhausted (e.g. `S07_dead_letter` where `max_attempts=1`), it safely degrades to `dead_letter_node` notifying the engineering team.
2. **Risky Actions Without Approval**: For sensitive requests like refunds or account deletions (`S04_risky`, `S06_delete`), direct execution poses severe business risk. The graph enforces a mandatory human-in-the-loop gate (`approval_node`). If rejected, it redirects to `ask_clarification_node` rather than executing unauthorized side effects.

## 6. Persistence & Recovery Evidence
The workflow integrates SQLite Checkpointer (`SqliteSaver` in WAL mode) to persist graph snapshots at every step:
- **Thread Isolation**: Each run is keyed by `thread_id` (e.g. `thread-S01_simple`), preventing state bleeding across user sessions.
- **Crash Recovery & Time Travel**: Because state checkpoints are committed to disk/memory before node execution, any interrupted run or process crash can resume seamlessly from the exact step where it stopped.

## 7. Extension Work
- **SQLite Checkpointer Extension**: Implemented custom adapter in `persistence.py` supporting `SqliteSaver` with automatic thread safety and write-ahead logging (WAL mode).
- **Dynamic LLM Environment Adaptation**: Enhanced `llm.py` to support deepseek/custom endpoints and `.env` loading.

## 8. Improvement Plan
If given more time to productionize this workflow, I would prioritize:
1. **Real-time HITL Web UI**: Integrate a Streamlit or Next.js dashboard utilizing LangGraph's `interrupt()` and `Command(resume=...)` API for interactive reviewer approvals.
2. **Parallel Tool Fan-out**: Use LangGraph `Send` API to execute multiple independent tool lookups concurrently to reduce end-to-end latency.
3. **Telemetry & Tracing**: Export structured audit `events` to LangSmith / OpenTelemetry for production observability and SLA monitoring.
