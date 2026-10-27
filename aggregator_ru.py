#!/usr/bin/env python3
"""
Aggregator for NC-Bench and NC-Bench-RU.
Supports two evaluation modes:
  1. '--mode strict' (default): Robust parsing, tracks missing/omitted tasks,
     computes both evaluated accuracy (on answered subset) and benchmark accuracy
     (penalizing omitted tasks with score 0), detects truncated outputs and judge errors.
  2. '--mode original': Replicates upstream IBM aggregator logic for bug-for-bug compatibility.
Works with standard Python (no pandas dependency required, though compatible).
"""
import argparse
import glob
import json
import os
import re
import string
import sys


STANDARD_BASIC_RAG_TASKS = [
    'definition request', 'example request', 'incremental request', 'inquiry',
    'inquiry ungrounded', 'incremental-self-correction', 'paraphrase request',
    'repeat request', 'self-correction', 'sequence abort', 'sequence closer'
]

STANDARD_COMPLEX_TASKS = [
    'Self-Correction', 'Recommendation-Compact', 'Recommendation-Expanded',
    'Recommendation-Incremental', 'Detail Request-Partial', 'Detail Request-All',
    'Detail Request-Expanded', 'Repeat', 'Partial Repeat', 'Paraphrase',
    'Example', 'Definition', 'Closer', 'Abort', 'Preliminary-Screen',
    'Preliminary-Detail', 'Expansion-Choices', 'Expansion-Repair'
]


def get_args():
    parser = argparse.ArgumentParser(description="Aggregate NC-Bench / NC-Bench-RU evaluation results.")
    parser.add_argument('--judgments_dir', type=str, required=True, help="Directory with judge output JSONL files.")
    parser.add_argument('--evaluations_dir', type=str, required=True, help="Directory to save evaluation reports.")
    parser.add_argument('--prompts_file', type=str, default=None,
                        help="Optional path to original prompts JSONL to anchor expected counts and detect missing tasks.")
    parser.add_argument('--mode', choices=['original', 'strict'], default='strict',
                        help="Scoring mode: 'strict' (robust parsing, tracks missing tasks) or 'original' (exact upstream IBM logic).")
    return parser.parse_args()


ALL_KNOWN_LABELS = {
    'Answer', 'NonAnswer', 'Repeat', 'Partial Repeat', 'Paraphrase', 'Definition', 'Example',
    'Acknowledgment', 'Acknowledgement', 'Appreciation', 'GratitudeReceipt', 'AppreciationReceipt',
    'Assessment', 'PreClosing', 'Apology', 'SequenceAbort', 'Silence', 'NewTopic', 'NonVerbal',
    'OOC', 'Other', 'DetailRequestGrounded', 'DetailRequestUngrounded', 'RepeatRequest',
    'ParaphraseRequest', 'DefinitionRequest', 'ExampleRequest', 'Affirmation', 'HelpOffer',
    'ChoiceGiving'
}


def assign_acceptable_answers(task):
    """Upstream IBM NC-Bench acceptable answers mapping."""
    if task in ['inquiry', 'incremental request', 'self-correction', 'Self-Correction', 'Recommendation-Compact', 'Recommendation-Expanded']:
        return ['Answer', 'NonAnswer', 'Definition', 'RepeatRequest', 'ParaphraseRequest', 'ExampleRequest', 'DefinitionRequest']
    elif task in ['Recommendation-Incremental']:
        return ['Answer', 'NonAnswer', 'Definition', 'RepeatRequest', 'ParaphraseRequest', 'ExampleRequest', 'DefinitionRequest', 'DetailRequestGrounded']
    elif task in ['inquiry ungrounded', 'incremental-self-correction']:
        return ['NonAnswer', 'RepeatRequest', 'ParaphraseRequest', 'ExampleRequest', 'DefinitionRequest']
    elif task in ['repeat request', 'Repeat', 'Partial Repeat']:
        return ['Repeat', 'Partial Repeat']
    elif task in ['paraphrase request', 'Paraphrase']:
        return ['Paraphrase', 'Definition', 'Example']
    elif task in ['definition request', 'Definition']:
        return ['Definition']
    elif task in ['example request', 'Example']:
        return ['Example']
    elif ('sequence closer' in task) or ('Closer' in task):
        return ['PreClosing', 'Silence', 'NewTopic', 'NonVerbal', 'Acknowledgment', 'Acknowledgement', 'Assessment', 'GratitudeReceipt', 'AppreciationReceipt']
    elif task in ['sequence abort', 'Abort']:
        return ['PreClosing', 'Silence', 'GratitudeReceipt', 'Acknowledgment', 'NewTopic', 'Apology']
    elif 'Detail Request' in task:
        return ['DetailRequestGrounded']
    elif 'Preliminary' in task:
        return ['Affirmation', 'Acknowledgment', 'Assessment', 'HelpOffer', 'DetailRequestGrounded']
    elif task == 'Expansion-Choices':
        return ['ChoiceGiving']
    elif task == 'Expansion-Repair':
        return ['Repeat', 'Partial Repeat', 'Paraphrase', 'Example', 'Definition']
    else:
        return []


def clean_label(raw_label):
    """Strips markdown asterisks, quotes, and punctuation around labels."""
    s = raw_label.strip()
    s = s.strip('*_`"\'')
    s = s.strip(string.punctuation)
    return s.strip()


def parse_judge_output(raw_output, mode='strict'):
    if not isinstance(raw_output, str):
        return []
    
    if mode == 'original':
        # Exact upstream: replace '\n' with ',' and split by ','
        return list(set([ans.strip() for ans in raw_output.replace('\n', ',').split(',') if ans]))
    
    # Strict mode: handle commas, newlines, markdown bullets, and punctuation
    cleaned_tokens = []
    normalized = raw_output.replace('\n', ',').replace(';', ',')
    for chunk in normalized.split(','):
        lbl = clean_label(chunk)
        if lbl:
            if lbl == 'Acknowledgement':
                lbl = 'Acknowledgment'
            cleaned_tokens.append(lbl)
    return list(set(cleaned_tokens))


def evaluate_rows(rows, mode='strict'):
    scored_rows = []
    unknown_labels_count = 0
    
    for row in rows:
        acceptable = assign_acceptable_answers(row.get('task', ''))
        raw_output = row.get('output', '')
        is_missing = row.get('is_missing', False) or (raw_output == '[empty]')
        answers_split = parse_judge_output(raw_output, mode=mode)
        
        # Check for unknown judge labels in strict mode
        if mode == 'strict':
            for ans in answers_split:
                if ans not in ALL_KNOWN_LABELS:
                    unknown_labels_count += 1

        # Missing task handling: missing answer is scored 0
        if is_missing:
            score = 0
        else:
            # Scoring logic
            if 'Silence' in acceptable or 'NonVerbal' in acceptable:
                if 'Silence' in answers_split or 'NonVerbal' in answers_split:
                    score = int(len(answers_split) == 1)
                else:
                    score = int(any(ans in acceptable for ans in answers_split))
            else:
                score = int(any(ans in acceptable for ans in answers_split))
            
        scored_row = dict(row)
        scored_row['is_missing'] = is_missing
        scored_row['acceptable_answers'] = acceptable
        scored_row['parsed_judge_output'] = answers_split
        scored_row['score'] = score
        scored_rows.append(scored_row)
        
    return scored_rows, unknown_labels_count


def load_expected_tasks_from_prompts(prompts_file):
    expected_counts = {}
    with open(prompts_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                task = item.get('task')
                if task:
                    expected_counts[task] = expected_counts.get(task, 0) + 1
    return expected_counts


def infer_expected_task_counts(tasks):
    # Detect whether tasks match Complex Request or Basic/RAG
    has_complex = any(t in STANDARD_COMPLEX_TASKS for t in tasks)
    if has_complex:
        return {t: 20 for t in STANDARD_COMPLEX_TASKS}
    else:
        # Basic or RAG has 9 tasks, 20 items each
        active_tasks = [t for t in tasks if t in STANDARD_BASIC_RAG_TASKS]
        if not active_tasks:
            active_tasks = tasks
        return {t: 20 for t in active_tasks}


def aggregate_scored_rows(scored_rows, mode='strict', unknown_labels=0, prompts_file=None):
    present_tasks = sorted(list(set(r['task'] for r in scored_rows if r.get('task'))))

    if prompts_file and os.path.isfile(prompts_file):
        expected_counts = load_expected_tasks_from_prompts(prompts_file)
    else:
        expected_counts = infer_expected_task_counts(present_tasks)

    all_tasks = sorted(list(set(present_tasks).union(set(expected_counts.keys()))))
    
    total_evaluated = len(scored_rows)
    total_expected = sum(expected_counts.values()) if expected_counts else total_evaluated
    missing_instances = max(0, total_expected - total_evaluated)
    coverage_ratio = round(total_evaluated / total_expected, 4) if total_expected > 0 else 1.0

    result = {
        "metadata": {
            "mode": mode,
            "evaluated_instances": total_evaluated,
            "expected_instances": total_expected,
            "missing_instances": missing_instances,
            "coverage_ratio": coverage_ratio,
            "unknown_judge_labels_count": unknown_labels
        },
        "tasks": {}
    }
    
    total_score = 0
    task_evaluated_ratios = []
    task_benchmark_ratios = []
    
    for task in all_tasks:
        task_rows = [r for r in scored_rows if r.get('task') == task]
        task_score = sum(r['score'] for r in task_rows)
        task_eval_count = len(task_rows)
        task_exp_count = expected_counts.get(task, task_eval_count)
        task_missing = max(0, task_exp_count - task_eval_count)
        
        task_eval_ratio = (task_score / task_eval_count) if task_eval_count > 0 else 0.0
        task_bench_ratio = (task_score / task_exp_count) if task_exp_count > 0 else 0.0
        
        result["tasks"][task] = {
            "score": task_score,
            "evaluated_count": task_eval_count,
            "expected_count": task_exp_count,
            "missing_count": task_missing,
            "evaluated_ratio": round(task_eval_ratio, 4),
            "benchmark_ratio": round(task_bench_ratio, 4)
        }
        total_score += task_score
        task_evaluated_ratios.append(task_eval_ratio)
        task_benchmark_ratios.append(task_bench_ratio)

    macro_eval_avg = sum(task_evaluated_ratios) / len(task_evaluated_ratios) if task_evaluated_ratios else 0.0
    macro_bench_avg = sum(task_benchmark_ratios) / len(task_benchmark_ratios) if task_benchmark_ratios else 0.0
    
    micro_eval_avg = (total_score / total_evaluated) if total_evaluated > 0 else 0.0
    micro_bench_avg = (total_score / total_expected) if total_expected > 0 else 0.0
    
    result["summary"] = {
        "coverage": coverage_ratio,
        "evaluated_accuracy": round(micro_eval_avg, 4),
        "benchmark_accuracy": round(micro_bench_avg, 4),
        "macro_evaluated_average": round(macro_eval_avg, 4),
        "macro_benchmark_average": round(macro_bench_avg, 4),
        "total_score": total_score,
        "evaluated_count": total_evaluated,
        "expected_count": total_expected,
        "missing_count": missing_instances
    }

    if missing_instances > 0:
        warning_msg = (
            f"INCOMPLETE EVALUATION: {missing_instances} of {total_expected} tasks were missing/omitted "
            f"(coverage: {coverage_ratio * 100:.1f}%). "
            f"Evaluated accuracy on answered subset: {micro_eval_avg * 100:.2f}%. "
            f"Benchmark accuracy (penalizing missing tasks with 0): {micro_bench_avg * 100:.2f}%."
        )
        result["summary"]["warning"] = warning_msg
        print(f"\n⚠️  {warning_msg}", file=sys.stderr)
    
    # Also provide backward-compatible flat format matching upstream aggregator.py
    if mode == 'original':
        flat_result = {}
        for task, data in result["tasks"].items():
            flat_result[task] = data["score"]
            flat_result[f"{task} count"] = data["evaluated_count"]
            flat_result[f"{task} ratio"] = data["evaluated_ratio"]
        if missing_instances > 0:
            flat_result["_warning"] = result["summary"].get("warning", "")
        return flat_result

    return result


def process_file(input_file, output_file, mode='strict', prompts_file=None):
    with open(input_file, 'r', encoding='utf-8') as f:
        rows = [json.loads(line) for line in f if line.strip()]
        
    scored_rows, unknown_labels = evaluate_rows(rows, mode=mode)
    results = aggregate_scored_rows(scored_rows, mode=mode, unknown_labels=unknown_labels, prompts_file=prompts_file)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Processed ({mode}): {output_file}")


def main():
    args = get_args()
    files = glob.glob(os.path.join(args.judgments_dir, '*.jsonl'))
    if not files:
        print(f"No .jsonl files found in {args.judgments_dir}")
        return

    for input_file in files:
        filename = os.path.basename(input_file)
        out_filename = filename.replace('.jsonl', f'_{args.mode}.json' if args.mode != 'original' else '.json')
        output_file = os.path.join(args.evaluations_dir, out_filename)
        process_file(input_file, output_file, mode=args.mode, prompts_file=args.prompts_file)


if __name__ == '__main__':
    main()
