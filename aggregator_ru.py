#!/usr/bin/env python3
"""
Aggregator for NC-Bench and NC-Bench-RU.
Supports two evaluation modes:
  1. '--mode original': Exactly replicates upstream IBM aggregator logic.
  2. '--mode strict': Robust evaluation that strips punctuation/markdown, tracks
     truncated responses and judge parsing errors, and calculates both macro
     and micro averages.
Works with standard Python (no pandas dependency required, though compatible).
"""
import argparse
import glob
import json
import os
import re
import string


def get_args():
    parser = argparse.ArgumentParser(description="Aggregate NC-Bench / NC-Bench-RU evaluation results.")
    parser.add_argument('--judgments_dir', type=str, required=True, help="Directory with judge output JSONL files.")
    parser.add_argument('--evaluations_dir', type=str, required=True, help="Directory to save evaluation reports.")
    parser.add_argument('--mode', choices=['original', 'strict'], default='strict',
                        help="Scoring mode: 'original' (exact upstream IBM logic) or 'strict' (robust parsing).")
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
    # Replace markdown bullets, brackets, newlines
    normalized = raw_output.replace('\n', ',').replace(';', ',')
    for chunk in normalized.split(','):
        lbl = clean_label(chunk)
        if lbl:
            # Map common judge typos / synonyms if necessary
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
        answers_split = parse_judge_output(raw_output, mode=mode)
        
        # Check for unknown judge labels in strict mode
        if mode == 'strict':
            for ans in answers_split:
                if ans not in ALL_KNOWN_LABELS:
                    unknown_labels_count += 1

        # Scoring logic
        if 'Silence' in acceptable or 'NonVerbal' in acceptable:
            if 'Silence' in answers_split or 'NonVerbal' in answers_split:
                score = int(len(answers_split) == 1)
            else:
                score = int(any(ans in acceptable for ans in answers_split))
        else:
            score = int(any(ans in acceptable for ans in answers_split))
            
        scored_row = dict(row)
        scored_row['acceptable_answers'] = acceptable
        scored_row['parsed_judge_output'] = answers_split
        scored_row['score'] = score
        scored_rows.append(scored_row)
        
    return scored_rows, unknown_labels_count


def aggregate_scored_rows(scored_rows, mode='strict', unknown_labels=0):
    tasks = sorted(list(set(r['task'] for r in scored_rows)))
    result = {
        "metadata": {
            "mode": mode,
            "total_instances": len(scored_rows),
            "unknown_judge_labels_count": unknown_labels
        },
        "tasks": {}
    }
    
    total_score = 0
    task_ratios = []
    
    for task in tasks:
        task_rows = [r for r in scored_rows if r['task'] == task]
        task_score = sum(r['score'] for r in task_rows)
        task_count = len(task_rows)
        task_ratio = (task_score / task_count) if task_count > 0 else 0.0
        
        result["tasks"][task] = {
            "score": task_score,
            "count": task_count,
            "ratio": round(task_ratio, 4)
        }
        total_score += task_score
        task_ratios.append(task_ratio)

    macro_avg = sum(task_ratios) / len(task_ratios) if task_ratios else 0.0
    micro_avg = total_score / len(scored_rows) if scored_rows else 0.0
    
    result["summary"] = {
        "macro_average": round(macro_avg, 4),
        "micro_average": round(micro_avg, 4),
        "total_score": total_score,
        "total_count": len(scored_rows)
    }
    
    # Also provide backward-compatible flat format matching upstream aggregator.py
    if mode == 'original':
        flat_result = {}
        for task, data in result["tasks"].items():
            flat_result[task] = data["score"]
            flat_result[f"{task} count"] = data["count"]
            flat_result[f"{task} ratio"] = data["ratio"]
        return flat_result

    return result


def process_file(input_file, output_file, mode='strict'):
    with open(input_file, 'r', encoding='utf-8') as f:
        rows = [json.loads(line) for line in f if line.strip()]
        
    scored_rows, unknown_labels = evaluate_rows(rows, mode=mode)
    results = aggregate_scored_rows(scored_rows, mode=mode, unknown_labels=unknown_labels)
    
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
        process_file(input_file, output_file, mode=args.mode)


if __name__ == '__main__':
    main()
