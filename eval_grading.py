import json
import sys
from pathlib import Path
from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.persistence import build_checkpointer

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_eval():
    data_path = Path("data/sample/grading_questions.json")
    questions = json.loads(data_path.read_text(encoding="utf-8"))
    
    checkpointer = build_checkpointer("memory", None)
    graph = build_graph(checkpointer=checkpointer)
    
    results = []
    correct_count = 0
    
    print(f"Running evaluation on {len(questions)} questions...")
    for idx, item in enumerate(questions, 1):
        q_id = item["id"]
        q_text = item["question"]
        must_any = item["must_contain_any"]
        must_not = item["must_not_contain"]
        
        state = {
            "thread_id": f"eval-{q_id}",
            "scenario_id": q_id,
            "query": q_text,
            "route": "",
            "risk_level": "unknown",
            "attempt": 0,
            "max_attempts": 3,
            "final_answer": None,
            "messages": [],
            "tool_results": [],
            "errors": [],
            "events": [],
        }
        
        run_config = {"configurable": {"thread_id": state["thread_id"]}}
        try:
            final_state = graph.invoke(state, config=run_config)
            ans = str(final_state.get("final_answer", "") or "")
            route = final_state.get("route", "")
        except Exception as e:
            ans = f"ERROR: {e}"
            route = "error"
            
        ans_lower = ans.lower()
        
        # Check criteria
        pass_any = len(must_any) == 0 or any(m.lower() in ans_lower for m in must_any)
        pass_not = len(must_not) == 0 or not any(m.lower() in ans_lower for m in must_not)
        is_passed = pass_any and pass_not
        
        if is_passed:
            correct_count += 1
            
        results.append({
            "id": q_id,
            "question": q_text,
            "route": route,
            "answer": ans,
            "must_contain_any": must_any,
            "must_not_contain": must_not,
            "pass_any": pass_any,
            "pass_not": pass_not,
            "passed": is_passed
        })
        print(f"[{idx}/{len(questions)}] {q_id}: route={route} | passed={is_passed}")
        if not is_passed:
            print(f"   -> Ans: {ans[:100]}...")
            print(f"   -> Expected any: {must_any}")
            
    print(f"\nFinal Score: {correct_count}/{len(questions)} ({correct_count/len(questions)*100:.1f}%)")
    
    out_file = Path("outputs/grading_results.json")
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved detailed results to {out_file}")

if __name__ == "__main__":
    run_eval()
