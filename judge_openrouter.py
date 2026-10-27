"""NC-Bench judge via OpenRouter. Uses stdlib only; --dry-run makes no API calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from openrouter_judge_prompts import build_judge_prompts

DEFAULT_JUDGE = "meta/muse-spark-1.3-contributor"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
ROOT = Path(__file__).resolve().parent


def local_config():
    values = {}
    path = ROOT / ".env.local"
    if path.exists():
        for line in path.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in {"OPENROUTER_API_KEY", "OPENROUTER_JUDGE_MODEL"}:
                values[key.strip()] = value.strip().strip("\"'")
    for key in ("OPENROUTER_API_KEY", "OPENROUTER_JUDGE_MODEL"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def read_rows(path):
    rows = {}
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        ident = row["id"]
        if ident in rows:
            raise ValueError(f"Duplicate ID {ident} in {path} at line {number}")
        rows[ident] = row
    return rows


def validate_inputs(prompts, generations):
    if not prompts:
        raise ValueError("Empty benchmark input")
    missing, extra = set(prompts) - set(generations), set(generations) - set(prompts)
    if missing or extra:
        raise ValueError(f"Incomplete generation set: {len(missing)} missing, {len(extra)} extra IDs")
    for ident, source in prompts.items():
        row = generations[ident]
        if row.get("task") != source["task"]:
            raise ValueError(f"Generation task mismatch for ID {ident}")
        if not isinstance(row.get("output"), str) or row.get("is_missing"):
            raise ValueError(f"Missing or invalid generation for ID {ident}")
        if row.get("finish_reason") in {"length", "error", "content_filter"}:
            raise ValueError(f"Incomplete/filtered generation for ID {ident}; review it before judging")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def request_judgment(messages, model, api_key, max_tokens, timeout):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens,
               "temperature": 0, "stream": False}
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        # Provider errors may echo request details; never log the body or headers.
        raise RuntimeError(f"OpenRouter HTTP {exc.code}; partial judgments preserved") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("OpenRouter network error; partial judgments preserved; no automatic retries") from None
    if data.get("error"):
        raise RuntimeError("OpenRouter returned an API error; partial judgments preserved")
    choice = data["choices"][0]
    output = choice["message"].get("content")
    if choice.get("finish_reason") != "stop":
        raise RuntimeError("Judge did not finish normally; truncated/filtered result excluded")
    if not isinstance(output, str) or not output.strip():
        raise RuntimeError("Judge returned no classification; empty judge output excluded")
    return {"output": output, "finish_reason": choice["finish_reason"],
            "requested_judge": model, "judge_model": data.get("model", model),
            "response_id": data.get("id"), "usage": data.get("usage", {})}


def run(args, transport=None):
    config = local_config()
    model = args.judge or config.get("OPENROUTER_JUDGE_MODEL") or DEFAULT_JUDGE
    prompts, generations = read_rows(args.prompts_file), read_rows(args.generations_file)
    validate_inputs(prompts, generations)
    judge_prompts = build_judge_prompts(prompts, generations, args.language)
    if {row["id"] for row in judge_prompts} != set(prompts) or len(judge_prompts) != len(prompts):
        raise ValueError("Judge prompt generator omitted or duplicated benchmark IDs")
    settings = {"judge": model, "endpoint": ENDPOINT, "language": args.language,
                "max_tokens": args.max_new_tokens, "temperature": 0,
                "prompts_sha256": sha(args.prompts_file), "generations_sha256": sha(args.generations_file),
                "judge_prompts_sha256": hashlib.sha256(json.dumps(judge_prompts, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                "expected_count": len(prompts), "response_scope": "full_response",
                "adapter": "openrouter_full_response_v1"}
    protocol_id = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "api_requests": 0, **settings}, ensure_ascii=False, indent=2))
        return settings
    api_key = config.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Set OPENROUTER_API_KEY or store it in the ignored .env.local file")
    output = Path(args.judgments_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    meta_path = output.with_suffix(output.suffix + ".meta.json")
    if (output.exists() or meta_path.exists()) and not args.resume:
        raise ValueError("Output already exists; use --resume with the same inputs and protocol")
    existing = read_rows(output) if output.exists() else {}
    if existing and not meta_path.exists():
        raise ValueError("Existing judgments have no protocol metadata; refusing to mix runs")
    if meta_path.exists():
        previous = json.loads(meta_path.read_text())
        if previous.get("protocol_id") != protocol_id:
            raise ValueError("Resume settings, inputs, or judge prompts differ from the original run")
    for ident, row in existing.items():
        if ident not in prompts or row.get("task") != prompts[ident]["task"] or row.get("protocol_id") != protocol_id:
            raise ValueError("Existing judgment ID/task/protocol mismatch")
    metadata = {**settings, "protocol_id": protocol_id, "status": "running", "completed_count": len(existing)}
    atomic_json(meta_path, metadata)
    transport = transport or request_judgment
    try:
        with output.open("a", encoding="utf-8") as stream:
            for row in judge_prompts:
                if row["id"] in existing:
                    continue
                result = transport(row["chat_prompt"], model, api_key, args.max_new_tokens, args.timeout)
                record = {"id": row["id"], "task": row["task"], "protocol_id": protocol_id, **result}
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                existing[row["id"]] = record
                metadata.update(completed_count=len(existing), updated_unix=time.time())
                atomic_json(meta_path, metadata)
                print(f"Judged {len(existing)}/{len(prompts)}", flush=True)
    except Exception as exc:
        # Keep credentials, request bodies, and response text out of metadata errors.
        metadata.update(status="failed", error_type=type(exc).__name__, completed_count=len(existing))
        atomic_json(meta_path, metadata)
        raise
    metadata.update(status="complete", completed_count=len(existing), judgments_sha256=sha(output))
    atomic_json(meta_path, metadata)
    print(f"Complete: {output}", flush=True)
    return metadata


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge", default=None, help="Default: " + DEFAULT_JUDGE)
    parser.add_argument("--prompts_file", default=str(ROOT / "data_ru/conversation_competence_ru.jsonl"))
    parser.add_argument("--generations_file", required=True)
    parser.add_argument("--judgments_file", required=True)
    parser.add_argument("--language", choices=["ru", "en"], default="ru")
    parser.add_argument("--max_new_tokens", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Validate input coverage and prepare judge prompts without network calls")
    return parser.parse_args()


if __name__ == "__main__":
    run(get_args())
