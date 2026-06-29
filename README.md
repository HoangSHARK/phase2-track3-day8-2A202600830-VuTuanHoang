# Hướng Dẫn Chạy Bài Lab — LangGraph Agentic Orchestration

Dự án này triển khai một hệ thống Agent hỗ trợ khách hàng (Support-ticket Agent) chuẩn production sử dụng kiến trúc **LangGraph StateGraph**. Hệ thống quản lý trạng thái có cấu trúc, định tuyến động (conditional routing), vòng lặp thử lại có giới hạn (bounded retry loop), duyệt tác vụ rủi ro bởi con người (HITL - Human-in-the-Loop), lưu trữ bền vững (SQLite Checkpointer) và thu thập độ đo tự động.

---

## 🚀 1. Yêu cầu Hệ thống & Cài đặt Môi trường

### Prerequisites
- **Python >= 3.11**
- Tài khoản API của nhà cung cấp LLM (DeepSeek, OpenAI, hoặc Google GenAI)

### Cài đặt thư viện phụ thuộc
Mở terminal tại thư mục gốc của dự án và chạy lệnh:

```bash
# Cài đặt gói dự án dưới dạng editable cùng các công cụ dev (pytest, ruff, mypy)
pip install -e ".[dev]"

# Cài đặt adapter SQLite Checkpointer cho LangGraph
pip install langgraph-checkpoint-sqlite
```

> **Lưu ý quan trọng trên Windows PowerShell:** Nếu bạn không muốn cài đặt dạng editable (`pip install -e .`), bạn cần thiết lập biến môi trường `PYTHONPATH` trước khi chạy các lệnh Python/pytest:
> ```powershell
> $env:PYTHONPATH="src"
> ```

---

## ⚙️ 2. Cấu hình Khóa API LLM (`.env`)

Hệ thống sử dụng mô hình ngôn ngữ lớn (LLM) cho các node phân loại ý định (`classify_node`), sinh câu trả lời (`answer_node`), và làm rõ câu hỏi (`ask_clarification_node`).

Bạn đã có sẵn file `.env` được cấu hình. Nếu cài đặt trên môi trường mới, hãy sao chép từ `.env.example`:

```bash
cp .env.example .env
```

**Cấu hình cho DeepSeek (OpenAI-compatible):**
```ini
OPENAI_API_KEY="sk-xxxx..."
OPENAI_BASE_URL="https://api.deepseek.com"
DEFAULT_MODEL="deepseek-chat"
```

---

## 🧪 3. Hướng dẫn Kiểm thử Tự động (Run Unit Tests)

Để đảm bảo toàn bộ các node, logic định tuyến và đồ thị hoạt động chính xác 100%, hãy chạy bộ kiểm thử tự động `pytest`:

**Cách 1: Sử dụng Make (Khuyên dùng trên Linux/macOS/Git Bash)**
```bash
make test
```

**Cách 2: Chạy trực tiếp qua PowerShell trên Windows**
```powershell
$env:PYTHONPATH="src"; pytest
```

Kết quả mong đợi (Toàn bộ 25 bài test đều vượt qua):
```text
.........................                                                [100%]
25 passed in ...s
```

---

## 🏃 4. Chạy Scenarios & Thu thập Độ đo (Run Scenarios)

Hệ thống cung cấp **7 tình huống mẫu (scenarios)** tại `data/sample/scenarios.jsonl` bao gồm các luồng: hỏi đáp đơn giản, tra cứu tool, thiếu thông tin, tác vụ rủi ro cần HITL duyệt, lỗi hệ thống và phục hồi lặp lại (retry).

Để mô phỏng đồ thị chạy qua 7 tình huống này và xuất độ đo ra file `outputs/metrics.json`:

**Sử dụng Make:**
```bash
make run-scenarios
```

**Hoặc chạy CLI bằng PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m langgraph_agent_lab.cli run-scenarios --config configs/lab.yaml --output outputs/metrics.json
```

> **🌟 Chạy Bộ kiểm thử Mở rộng (Custom Scenarios):** Ngoài bộ dữ liệu mẫu, dự án đi kèm bộ 8 kịch bản kiểm thử mở rộng (`data/sample/scenarios_custom.jsonl`). Bạn có thể mô phỏng và thu nhận độ đo cho bộ test này bằng lệnh:
> ```powershell
> $env:PYTHONPATH="src"; python -m langgraph_agent_lab.cli run-scenarios --config configs/custom.yaml --output outputs/metrics_custom.json
> ```

---

## 📈 5. Chấm điểm & Đánh giá Kết quả (Validate Metrics)

Sau khi chạy xong kịch bản mô phỏng, kiểm tra và chấm điểm tự động bộ độ đo vừa sinh ra:

**Sử dụng Make:**
```bash
make grade-local
```

**Hoặc chạy CLI bằng PowerShell:**
```powershell
$env:PYTHONPATH="src"; python -m langgraph_agent_lab.cli validate-metrics --metrics outputs/metrics.json
```

Kết quả mong đợi:
```text
Metrics valid. success_rate=100.00%
```

---

## 📑 6. Báo Cáo & Dữ Liệu Lịch Sử

Sau khi hoàn tất quá trình chạy scenarios, hệ thống tự động sinh ra các tài liệu và dữ liệu kiểm chứng:

1. **Báo cáo tổng hợp Lab Report**: Xem tại `reports/lab_report.md`. Báo cáo chứa bảng tổng kết kết quả của 7 scenario, giải thích kiến trúc State schema, phân tích lỗi (failure analysis), và kế hoạch cải tiến.
2. **Cơ sở dữ liệu SQLite (Persistence)**: Được lưu tại `outputs/checkpoints.db` (chạy ở chế độ WAL tự động an toàn luồng). Mỗi kịch bản được lưu vết snapshot theo `thread_id` (ví dụ: `thread-S01_simple`), cho phép phục hồi trạng thái và khôi phục sau sự cố (crash-resume).
3. **Báo cáo Đánh giá Nghiệp vụ Nội bộ (Grading Report)**: Xem tại `reports/grading_dataset_report.md`. Báo cáo kiểm chứng chi tiết 10 câu hỏi nghiệp vụ từ bộ dữ liệu `data/sample/grading_questions.json` với tỷ lệ chính xác đạt **100%** (10/10 câu đạt chuẩn bộ lọc tiêu chí). Bạn có thể chạy lại đánh giá này bằng lệnh:
   ```powershell
   $env:PYTHONPATH="src"; python eval_grading.py
   ```
   Kết quả chấm điểm tự động xuất ra tại `outputs/grading_results.json`.

---

## 🏛️ 7. Kiến Trúc Luồng Đồ Thị LangGraph

```text
START 
  │
  ▼
[intake] ───► [classify] ──┬──(simple)───────► [answer] ───────────────────┐
                           ├──(tool)─────────► [tool] ◄──┐                 │
                           ├──(missing_info)─► [clarify] │                 │
                           ├──(risky)────────► [risky_action]              │
                           └──(error)────────► [retry] ──┴──(attempt < max)│
                                                 │                         │
            ┌────────────────────────────────────┘                         │
            ▼ (attempt >= max)                                             │
      [dead_letter] ───────────────────────────────────────────────────────┤
            ▲                                                              │
            │ (evaluation_result == "needs_retry")                         │
         [evaluate] ◄── [tool] ◄──(approved)── [approval] ◄─ [risky_action]│
            │                         ▲                                    │
            │ (success)               └───(rejected)──► [clarify] ─────────┤
            ▼                                                              │
         [answer] ─────────────────────────────────────────────────────────┴──► [finalize] ──► END
```
