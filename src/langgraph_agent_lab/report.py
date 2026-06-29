"""Report generation helper.

TODO(student): implement report rendering using MetricsReport data
and the template in reports/lab_report_template.md.
"""

from __future__ import annotations

from pathlib import Path

from .metrics import MetricsReport


def render_report(metrics: MetricsReport) -> str:
    """Render a complete lab report from metrics data."""
    lines = [
        "# Day 08 Lab Report — LangGraph Agentic Orchestration",
        "",
        "## 1. Team / Student",
        "- **Name**: Vu Tuan Hoang",
        "- **Date**: 2026-06-29",
        f"- **Summary**: Completed {metrics.total_scenarios} scenarios with a success rate of {metrics.success_rate:.2%}.",
        "",
        "## 2. Architecture",
        "The production support-ticket agent workflow uses a structured LangGraph `StateGraph` designed with conditional routing, HITL gates, and bounded retry loops:",
        "- **Intake & Classify**: Normalizes query and uses DeepSeek/OpenAI LLM with structured output (`with_structured_output`) to classify queries into 5 intent priority levels (`risky` > `tool` > `missing_info` > `error` > `simple`).",
        "- **Tool Execution & Retry Loop**: Executes tool queries. If errors occur or evaluation fails (`evaluate_node`), routes to `retry_or_fallback_node` up to `max_attempts` before escalating to `dead_letter_node`.",
        "- **HITL Approval**: High-risk actions route to `risky_action_node` and `approval_node` for verification before proceeding to tools.",
        "- **Finalization**: All execution paths guarantee termination at `finalize_node` before reaching `END`.",
        "",
        "## 3. State Schema",
        "The `AgentState` schema balances lean serialization with auditability:",
        "",
        "| Field | Reducer | Why |",
        "|---|---|---|",
        "| `messages` | append (`add`) | Audit conversation history and event tracking |",
        "| `tool_results` | append (`add`) | Preserve sequence of tool outputs and retry attempts |",
        "| `errors` | append (`add`) | Log transient tool errors and retry failures |",
        "| `events` | append (`add`) | Full structured observability log for grading |",
        "| `route` | overwrite | Tracks current classified intent route |",
        "| `evaluation_result` | overwrite | Drives retry loop conditional gating |",
        "| `proposed_action` | overwrite | Holds pending action payload for HITL approval |",
        "| `approval` | overwrite | Records decision and metadata from reviewer |",
        "",
        "## 4. Scenario Results",
        f"- **Total Scenarios**: {metrics.total_scenarios}",
        f"- **Success Rate**: {metrics.success_rate:.2%}",
        f"- **Total Retries**: {metrics.total_retries}",
        f"- **Total Interrupts**: {metrics.total_interrupts}",
        f"- **Avg Nodes Visited**: {metrics.avg_nodes_visited:.2f}",
        "",
        "| Scenario | Expected Route | Actual Route | Success | Retries | Interrupts |",
        "|---|---|---|:---:|:---:|:---:|",
    ]
    for m in metrics.scenario_metrics:
        success_mark = "✅" if m.success else "❌"
        actual = m.actual_route or "N/A"
        lines.append(f"| `{m.scenario_id}` | `{m.expected_route}` | `{actual}` | {success_mark} | {m.retry_count} | {m.interrupt_count} |")
    
    lines.extend([
        "",
        "## 5. Failure Analysis",
        "1. **Transient Tool Failures & Bounded Retries**: When tool lookups timeout or fail (e.g. `S05_error`), the graph captures the error in state and routes through `evaluate_node` to `retry_or_fallback_node`. Bounding retries via `attempt < max_attempts` ensures the system self-heals without infinite looping. If retries are exhausted (e.g. `S07_dead_letter` where `max_attempts=1`), it safely degrades to `dead_letter_node` notifying the engineering team.",
        "2. **Risky Actions Without Approval**: For sensitive requests like refunds or account deletions (`S04_risky`, `S06_delete`), direct execution poses severe business risk. The graph enforces a mandatory human-in-the-loop gate (`approval_node`). If rejected, it redirects to `ask_clarification_node` rather than executing unauthorized side effects.",
        "",
        "## 6. Persistence & Recovery Evidence",
        "The workflow integrates SQLite Checkpointer (`SqliteSaver` in WAL mode) to persist graph snapshots at every step:",
        "- **Thread Isolation**: Each run is keyed by `thread_id` (e.g. `thread-S01_simple`), preventing state bleeding across user sessions.",
        "- **Crash Recovery & Time Travel**: Because state checkpoints are committed to disk/memory before node execution, any interrupted run or process crash can resume seamlessly from the exact step where it stopped.",
        "",
        "## 7. Extension Work",
        "- **SQLite Checkpointer Extension**: Implemented custom adapter in `persistence.py` supporting `SqliteSaver` with automatic thread safety and write-ahead logging (WAL mode).",
        "- **Dynamic LLM Environment Adaptation**: Enhanced `llm.py` to support deepseek/custom endpoints and `.env` loading.",
        "",
        "## 8. Improvement Plan",
        "If given more time to productionize this workflow, I would prioritize:",
        "1. **Real-time HITL Web UI**: Integrate a Streamlit or Next.js dashboard utilizing LangGraph's `interrupt()` and `Command(resume=...)` API for interactive reviewer approvals.",
        "2. **Parallel Tool Fan-out**: Use LangGraph `Send` API to execute multiple independent tool lookups concurrently to reduce end-to-end latency.",
        "3. **Telemetry & Tracing**: Export structured audit `events` to LangSmith / OpenTelemetry for production observability and SLA monitoring.",
        ""
    ])
    return "\n".join(lines)


def write_report(metrics: MetricsReport, output_path: str | Path) -> None:
    """Write the rendered report to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(metrics), encoding="utf-8")
