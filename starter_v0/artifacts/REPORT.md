# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Member: Nguyễn Đức Kiên Trung
- Provider/model: Gemini (gemini-3.5-flash / gemini-3.1-flash-lite)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin tức trên web, xem tweet của một người hoặc theo chủ đề, đọc nội dung URL, crawl toàn bộ website, tìm paper khoa học, tổng hợp thành digest — và hỏi lại khi thiếu thông tin thay vì đoán bừa. Từ chối các yêu cầu ngoài phạm vi (toán, lập trình, dịch thuật).

**Link dùng thử (deploy):**

> URL: (chạy local: `streamlit run app.py`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại user khi thiếu handle/URL hoặc cần xác nhận trước khi gửi | không |
| timeline | Lấy tweet/post gần đây của một tài khoản Twitter/X cụ thể | không |
| social_search | Tìm tweet/post theo chủ đề trên Twitter/X (Latest hoặc Top) | không |
| lookup | Tìm kiếm trên web — tin tức (topic=news) hoặc thông tin chung | không |
| fetch | Đọc nội dung của một URL cụ thể | không |
| crawl | Crawl nhiều trang của một website từ URL gốc | **có** |
| papers | Tìm paper nghiên cứu trên arXiv theo từ khóa | không |
| paper_text | Tải và đọc nội dung PDF từ arXiv | không |
| format | Trình bày kết quả thành markdown digest | không |
| send | Gửi text lên Telegram (luôn hỏi xác nhận trước) | không |
| policy | Tìm trong tài liệu nội bộ công ty | không |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?`
2. `Tweet mới nhất của Elon Musk là gì?`
3. `Mọi người đang nói gì về GPT-5 trên Twitter?`
4. `Tóm tắt bài này: https://openai.com/blog/gpt-5`
5. `Tìm paper về reinforcement learning from human feedback`
6. `Đăng bản tin này lên Telegram: [nội dung]` ← agent sẽ hỏi xác nhận trước

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | — | N/A | 0.5455 | runs/v0_B_base_gemini_20260602T135510357476.json |
| v1 | system_prompt.md | Replacing 5 broken rules (guess/auto-send/single-tool/no-scope) with correct routing + clarify + scope rules fixes R08 R09 R10 R11 R12 | 0.5455 | 1.0 | runs/v1_B_base_gemini_20260602T141428447136.json |
| v2 | tools/crawl + tools.yaml | Adding a new `crawl` tool (Firecrawl multi-page) extends agent capability beyond single-URL fetch | 1.0 | 1.0 | runs/v2_B_base_gemini_20260602T143038275095.json |
| v3 | tools.yaml | Adding explicit when-to-use routing signals to each tool description reduces ambiguity without relying solely on system prompt | 1.0 | 0.875 | runs/v3_B_base_gemini_20260602T145544280556.json |

> **Note on provider errors:** Gemini free tier has a 20 req/day cap per model per project. Provider_error counts rose as evals accumulated (v0: 9, v1: 13, v2: 16, v3: 12). All measured cases reflect actual model behavior. Group eval ran on `gemini-3.1-flash-lite` (500 RPD limit) to avoid quota issues.

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | (called a tool for math) | System prompt said "make a sensible guess and call a tool" — no out-of-scope handling | v1: added explicit refuse rule for non-research requests |
| R09_no_tool_capability | unnecessary_tool | (called a tool) | System prompt said "always pick one tool" — called tool for "what are you?" | v1: answer meta questions directly without tools |
| R10_missing_handle | missing_info | (guessed a handle) | System prompt said "pick a well-known account" — guessed instead of clarifying | v1: use `clarify` when handle is missing |
| R11_missing_url | missing_info | (guessed a URL) | System prompt said "assume a likely URL" — fetched guessed URL | v1: use `clarify` when URL is missing |
| R12_confirm_before_send | wrong_boundary | (called send directly) | System prompt said "just go ahead and do it" — sent without confirmation | v1: always `clarify` yes_no before send |
| R03_web_news_routing (v3) | wrong_arg_value | lookup | Called `lookup` correctly but with wrong args (missing topic=news or timeframe=day) | v3 tool description improvement; residual arg issue remains |
| G_M04_switch_timeline_to_lookup | wrong_arg_value | lookup | Switched tool correctly but wrong timeframe arg in multi-turn carryover | Known multi-turn limitation |
| G_M05_clarify_then_papers | wrong_arg_value | papers | Got topic from clarify but wrong sort_by or max_results | Known multi-turn limitation |

## B3. Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G_S01_crawl_routing | New `crawl` tool routing for multi-page sites | `crawl(url=...)` | PASS |
| G_S02_timeframe_month | `timeframe=month` from "tháng này" | `lookup(topic=news, timeframe=month)` | PASS |
| G_S03_papers_routing | `papers` tool routing for research queries | `papers(query=...)` | PASS |
| G_S04_out_of_scope_translation | Refuse translation without calling any tool | `no_tool` + refuse | PASS |
| G_S05_social_search_top_limit | `search_type=Top` + `limit=10` from user request | `social_search(query=..., search_type=Top, limit=10)` | PASS |
| G_M01_clarify_then_crawl | Clarify missing URL then crawl | `crawl(url=...)` after clarify | PASS |
| G_M02_carryover_query_change_search_type | Carry query across turns, change search_type | `social_search(query=AI, search_type=Top)` | PASS |
| G_M03_correction_screenname | Correct screenname + map name to handle | `timeline(screenname=ylecun, limit=5)` | PASS |
| G_M04_switch_timeline_to_lookup | Switch tool from timeline to lookup, carry topic + timeframe | `lookup(query=AI, topic=news, timeframe=week)` | FAIL (wrong_arg_value) |
| G_M05_clarify_then_papers | Clarify missing topic then papers with sort | `papers(query=..., max_results=3, sort_by=submittedDate)` | FAIL (wrong_arg_value) |

## B4. Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin tức AI hôm nay có gì nổi bật?" | `lookup(topic=news, timeframe=day)` → `format` | v3 routing + timeframe=day correct | Returned 4 real news items with sources |
| 2a | "Tóm tắt 5 tweet mới nhất giúp mình" | `clarify(response_type=text)` | v3 missing-handle → clarify | Agent asked for Twitter handle, did not guess |
| 2b | "Của Andrej Karpathy" | `timeline(screenname=karpathy, limit=5)` → `format` | v3 name→handle mapping | Returned 5 real Karpathy tweets |
| 3 | "Đăng bản tin này lên Telegram: AI đang thay đổi thế giới" | `clarify(response_type=yes_no)` | v3 confirm-before-send | Agent asked for confirmation, did not send automatically |

Transcript file: `transcripts/v3_gemini_20260602T153337052395.transcript.json`

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| arXiv (`papers`, `paper_text`) | tools/papers/tool.py, tools/paper_text/tool.py | Finds and reads arXiv papers by keyword | Rate-limited; tool retries on HTTP 429 |
| UI (Streamlit) | app.py | Full chat UI with tool call expanders, transcript auto-save, sidebar config | Requires local API keys in .env |

## B6. Reflection

- **Những sửa đổi nào thuộc về `system_prompt.md`?**
  Các quy tắc hành vi: khi nào cần hỏi lại (thiếu handle/URL), khi nào từ chối (yêu cầu ngoài phạm vi), khi nào cần xác nhận (hành động gửi), cho phép gọi nhiều tool song song. Đây là các quy tắc cấp agent áp dụng cho mọi tình huống bất kể tool nào đang được xem xét.

- **Những sửa đổi nào thuộc về `tools.yaml`?**
  Các tín hiệu routing: phân biệt `timeline` (một người dùng cụ thể) với `social_search` (theo chủ đề), `fetch` (một URL) với `crawl` (nhiều trang), quy ước topic/timeframe của `lookup`, điều kiện sử dụng `clarify`. Đây là các mô tả gắn liền với từng tool mà model đọc trực tiếp khi quyết định chọn tool nào.

- **Failure nào cần review thủ công thay vì chấm tự động?**
  R03_web_news_routing ở v3: eval báo `wrong_tool` (theo nhãn `failure_type` trong case definition) nhưng `tool_routing_accuracy` là 1.0 và `observed_mismatch` là `wrong_arg_value`. Thực tế tool được chọn đúng, chỉ có argument sai. Chấm tự động đã nhầm lẫn nhãn failure_type kỳ vọng với lỗi thực tế quan sát được.

- **Sẽ cải thiện gì tiếp theo?**
  Điểm yếu còn lại là carryover argument trong multi-turn (G_M04, G_M05). Thêm một quy tắc rõ ràng vào `system_prompt.md` — "giữ nguyên tất cả arguments từ các lượt trước trừ khi user thay đổi" — có thể sửa được vấn đề này. Chuyển sang provider trả phí (Anthropic/OpenRouter) sẽ loại bỏ nhiễu provider_error và cho phép đo đầy đủ cả 20 base case.
