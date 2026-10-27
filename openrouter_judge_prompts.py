"""Full-response transcript adapter; reuses the fork's existing label definitions."""
import importlib


def definition_name(task):
    if task in {"inquiry", "incremental request", "inquiry ungrounded", "incremental-self-correction"}:
        return "def_inquiry"
    direct = {"repeat request": "def_repeat", "paraphrase request": "def_para",
              "definition request": "def_def", "example request": "def_example",
              "sequence abort": "def_abort", "self-correction": "def_correction"}
    if task in direct:
        return direct[task]
    if task.startswith("sequence closer"):
        return "def_closer"
    if task in {"Self-Correction", "Recommendation-Compact", "Recommendation-Expanded", "Recommendation-Incremental", "Detail Request-Partial", "Detail Request-All", "Detail Request-Expanded"}:
        return "def_correction_open_request"
    if task in {"Repeat", "Partial Repeat"}:
        return "def_repeat_open_request"
    if task in {"Paraphrase", "Example", "Definition"}:
        return "def_repair_open_request"
    if task in {"Closer", "Abort"}:
        return "def_closer_open_request"
    if task in {"Preliminary-Screen", "Preliminary-Detail"}:
        return "def_preliminary_open_request"
    if task in {"Expansion-Choices", "Expansion-Repair"}:
        return "def_expansion_open_request"
    raise ValueError("Unknown benchmark category: " + task)


def build_judge_prompts(prompts, generations, language):
    # Import definitions only; do not depend on the mutable generic judge runner.
    definitions = importlib.import_module("utils_ru" if language == "ru" else "utils")
    suffix = "_ru" if language == "ru" else ""
    system = getattr(definitions, "sys_prompt" + suffix)
    template = getattr(definitions, "judge_prompt" + suffix)
    result = []
    for ident, source in prompts.items():
        turns = source["chat_prompt"]
        if not turns:
            raise ValueError("Empty conversation for benchmark ID " + str(ident))
        transcript, previous_agent = [], ""
        for number, turn in enumerate(turns):
            if turn["role"] == "user":
                transcript.append(f"{number} USER: {turn['content']}")
            elif turn["role"] in {"assistant", "agent"}:
                transcript.append(f"{number} AGENT: {turn['content']}")
                previous_agent = ("строка " if language == "ru" else "line ") + str(number)
        # All sentences survive. One numbered transcript turn prevents the
        # model's own newlines being mistaken for additional transcript turns.
        output = " ".join(generations[ident]["output"].splitlines()).strip()
        transcript.append(f"{len(turns)} AGENT: {output}")
        details = source.get("request_details") or ""
        text = (template.replace("<labels>", getattr(definitions, definition_name(source["task"]) + suffix).strip())
                .replace("<last_agent_turn_num>", str(len(turns)))
                .replace("<transcript_with_turn_num>", "\n".join(transcript))
                .replace("<prior_turn>", previous_agent)
                .replace("<request_details>", details))
        result.append({"id": ident, "task": source["task"], "chat_prompt": [
            {"role": "system", "content": system}, {"role": "user", "content": text}]})
    return result
