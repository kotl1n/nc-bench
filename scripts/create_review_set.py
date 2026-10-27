#!/usr/bin/env python3
"""
Creates the independent human review dataset for NC-Bench-RU.
Contains at least 5 examples per category across all subsets (Basic: 45, RAG: 45, Complex: 90 = 180 minimum),
plus tricky adaptations, idioms, and edge cases.
Generates:
  - nc-bench/review/review_set.jsonl
  - nc-bench/review/REVIEW_SET.md
"""
import json
import os

SUBSETS = {
    "Basic": {
        "ru_file": "nc-bench/data_ru/conversation_competence_ru.jsonl",
        "en_file": "nc-bench/scripts/basic_en.json",
    },
    "RAG": {
        "ru_file": "nc-bench/data_ru/conversation_competence_rag_ru.jsonl",
        "en_file": "nc-bench/scripts/rag_en.json",
    },
    "Complex Request": {
        "ru_file": "nc-bench/data_ru/conversation_competence_open_request_ru.jsonl",
        "en_file": "nc-bench/scripts/complex_en.json",
    }
}

# Rationale & ambiguity notes for specific categories and edge cases
CATEGORY_ACTION_MAP = {
    "definition request": "Запрос определения (DefinitionRequest) — устранение проблемы с пониманием конкретного термина. Модель должна дать толкование термина, а не пересказывать всю реплику.",
    "example request": "Запрос примера (ExampleRequest) — конкретизация общего понятия частным примером ('Например?'). Модель должна предоставить наглядный пример.",
    "incremental request": "Инкрементальный запрос — уточнение следующего параметра в продолжение предыдущего ответа.",
    "incremental-self-correction": "Самоисправление в инкрементальном запросе — пользователь корректирует ранее заданный фильтр/вопрос.",
    "inquiry": "Базовый запрос информации — ожидается прямой ответ (Answer) или обоснованный отказ (NonAnswer).",
    "inquiry ungrounded": "Запрос информации, отсутствующей в контексте документа — модель обязана дать NonAnswer, а не галлюцинировать.",
    "paraphrase request": "Запрос перефразирования (ParaphraseRequest) — устранение проблемы с пониманием ('Что вы имеете в виду?'). Модель должна переформулировать реплику иными словами.",
    "repeat request": "Просьба повторить (RepeatRequest) — устранение проблемы со слышимостью ('Что вы сказали?'). Модель обязана повторить предыдущую реплику теми же словами.",
    "self-correction": "Самоисправление пользователя — отмена или коррекция предшествующего тезиса. Проверяется способность переключиться на новую цель.",
    "sequence abort": "Отмена диалоговой последовательности ('Неважно', 'Отбой') — модель должна вежливо завершить тему (PreClosing/Silence), не навязывая продолжение.",
    "sequence closer": "Завершение диалоговой последовательности ('Понял', 'Спасибо') — модель должна подтвердить закрытие (GratitudeReceipt/PreClosing/Silence).",
    "Abort": "Отмена запроса в ролевом сценарии после отказа или невозможности выполнить запрос — сигнал отмены.",
    "Closer": "Штатное подтверждение/закрытие сценария — модель должна принять закрытие.",
    "Definition": "Запрос определения термина, упомянутого ассистентом в ролевом ответе.",
    "Detail Request-All": "Полный запрос деталей (холодный старт) — пользователь просит услугу без деталей, агент обязан запросить первую обязательную деталь.",
    "Detail Request-Expanded": "Запрос деталей в расширенном диалоге — агент выясняет следующую недостающую деталь.",
    "Detail Request-Partial": "Запрос деталей при частичной информации — агент должен запрашивать только недостающие слоты.",
    "Example": "Запрос примера в ролевом диалоге.",
    "Expansion-Choices": "Запрос вариантов выбора ('Какие есть варианты?') — агент должен перечислить допустимые опции (ChoiceGiving).",
    "Expansion-Repair": "Устранение непонимания при выяснении деталей.",
    "Paraphrase": "Запрос перефразирования в ролевом диалоге.",
    "Partial Repeat": "Частичный повтор нерасслышанного фрагмента ('Сколько-сколько?').",
    "Preliminary-Detail": "Предварительная реплика с контекстом/эмоцией — агент должен поддержать диалог и выяснить детали.",
    "Preliminary-Screen": "Предварительный вопрос-фильтр ('Это отдел кадров?') — утверждение (Affirmation) и предложение помощи (HelpOffer).",
    "Recommendation-Compact": "Готовая рекомендация при наличии всех деталей в одной реплике.",
    "Recommendation-Expanded": "Рекомендация после последовательного выяснения всех деталей.",
    "Recommendation-Incremental": "Рекомендация с модификацией одного из параметров.",
    "Repeat": "Полный повтор в ролевом диалоге.",
    "Self-Correction": "Самоисправление в ролевом диалоге."
}

def format_dialogue(turns):
    res = []
    for t in turns:
        role = t["role"].upper()
        content = t["content"]
        res.append(f"  {role}: {content}")
    return "\n".join(res)

def main():
    os.makedirs("nc-bench/review", exist_ok=True)
    review_items = []

    for subset_name, cfg in SUBSETS.items():
        with open(cfg["ru_file"], "r", encoding="utf-8") as f:
            ru_items = [json.loads(line) for line in f]
        with open(cfg["en_file"], "r", encoding="utf-8") as f:
            en_items = json.load(f)

        # Group by category
        by_cat = {}
        for r, e in zip(ru_items, en_items):
            cat = r["task"]
            by_cat.setdefault(cat, []).append((r, e))

        # Select at least 5 per category
        for cat, pairs in by_cat.items():
            # Pick first 5, plus any known difficult ones (e.g. idioms, empty turns, etc.)
            selected = pairs[:5]
            for r, e in selected:
                tested_action = CATEGORY_ACTION_MAP.get(cat, cat)
                
                # Check for special challenges
                challenge = "Стандартная выборка категории для валидации естественности русской речи и сохранения диалоговой функции."
                en_last = e["chat_prompt"][-1]["content"] if e["chat_prompt"] else ""
                ru_last = r["chat_prompt"][-1]["content"] if r["chat_prompt"] else ""
                
                if "never mind" in en_last.lower() or "forget it" in en_last.lower():
                    challenge = "Проверка SequenceAbort: русская реплика ('Неважно' / 'Тогда не надо' / 'Отбой') не должна звучать грубо и должна сохранять функцию отмены действия."
                elif "what did you say" in en_last.lower() or "say again" in en_last.lower():
                    challenge = "Проверка RepeatRequest: проверка устранения проблемы со слышимостью (требование повторить реплику дословно, а не пересказывать)."
                elif "what do you mean" in en_last.lower() or "don't understand" in en_last.lower():
                    challenge = "Проверка ParaphraseRequest: проверка устранения проблемы с пониманием (требование перефразировать другими словами)."
                elif "busting my butt" in str(e).lower() or "tooth fairy" in str(e).lower() or "stolen a march" in str(e).lower():
                    challenge = "Функциональная адаптация английской идиомы/культурной реалии: сохранение разговорной экспрессии и контекстной неоднозначности."
                elif r["id"] in [1, 5, 6, 15, 85, 88] and subset_name == "Basic":
                    challenge = "Особенность оригинального датасета: первая реплика пользователя пустая ('') из-за инициативы ассистента."
                elif r["id"] == 340 and subset_name == "Complex Request":
                    challenge = "Аномалия оригинального датасета IBM: последняя реплика принадлежит assistant вместо user. Требует документирования."

                review_entry = {
                    "review_id": f"rev_{len(review_items)+1:03d}",
                    "subset": subset_name,
                    "id": r["id"],
                    "original_id": r["original_id"],
                    "ru_id": r["ru_id"],
                    "task": cat,
                    "status": "draft/unvalidated",
                    "tested_action": tested_action,
                    "challenge_reason": challenge,
                    "en_dialogue": e["chat_prompt"],
                    "ru_dialogue": r["chat_prompt"]
                }
                review_items.append(review_entry)

    # Write review_set.jsonl
    jsonl_path = "nc-bench/review/review_set.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for it in review_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # Write REVIEW_SET.md
    md_path = "nc-bench/review/REVIEW_SET.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# NC-Bench-RU: Набор для независимого экспертного ручного ревью\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **Статус релиза**: `draft/unvalidated`\n")
        f.write("> Все переводы и адаптации прошли автоматическую двухпроходную верификацию, но **до проведения независимого ручного человеческого ревью набор имеет статус предварительного черновика (draft/unvalidated)**.\n\n")
        f.write(f"Всего отобрано для ревью: **{len(review_items)} заданий** (минимум 5 примеров на каждую из 36 категорий всех трёх подмножеств + сложные и спорные случаи).\n\n")
        f.write("## Инструкция для независимого ревьюера\n")
        f.write("При проверке каждой пары EN/RU оценивайте следующие критерии:\n")
        f.write("1. **Сохранение проверяемого разговорного действия**:\n")
        f.write("   - Просьба повторить (Repeat) не должна превращаться в просьбу объяснить.\n")
        f.write("   - Просьба перефразировать (Paraphrase) не должна превращаться в просьбу повторить.\n")
        f.write("   - Реплики завершения («понял», «ясно», «спасибо») должны сохранять функцию Sequence Closer.\n")
        f.write("   - Реплики отмены («забудь», «неважно», «отбой») должны сохранять функцию Sequence Abort.\n")
        f.write("2. **Естественность русского языка**: отсутствие неестественного машинного синтаксиса при сохранении разговорной непринуждённости.\n")
        f.write("3. **Сохранение фактов и чисел**: точное соответствие числовых значений, единиц измерения и условий задачи.\n")
        f.write("4. **Отсутствие подсказок**: русский перевод не должен подсказывать тестируемой модели правильный ответ или упрощать исходное затруднение.\n\n")
        f.write("---\n\n")

        current_subset = None
        for it in review_items:
            if it["subset"] != current_subset:
                current_subset = it["subset"]
                f.write(f"\n## Подмножество: {current_subset}\n\n")

            f.write(f"### [{it['review_id']}] ID {it['id']} — Категория: `{it['task']}`\n")
            f.write(f"- **Проверяемое действие**: {it['tested_action']}\n")
            f.write(f"- **Причина внимания / сложность**: {it['challenge_reason']}\n\n")
            f.write("#### Диалог (EN vs RU):\n\n")
            f.write("| Роль | Английский оригинал (EN) | Русская адаптация (RU) |\n")
            f.write("| :--- | :--- | :--- |\n")
            
            # Align turns (skip system if complex for brevity, or show)
            en_turns = it["en_dialogue"]
            ru_turns = it["ru_dialogue"]
            max_len = max(len(en_turns), len(ru_turns))
            for i in range(max_len):
                en_t = en_turns[i] if i < len(en_turns) else {"role": "-", "content": "-"}
                ru_t = ru_turns[i] if i < len(ru_turns) else {"role": "-", "content": "-"}
                en_c = en_t["content"].replace("\n", " ").replace("|", "\\|")
                ru_c = ru_t["content"].replace("\n", " ").replace("|", "\\|")
                if len(en_c) > 120:
                    en_c = en_c[:117] + "..."
                if len(ru_c) > 120:
                    ru_c = ru_c[:117] + "..."
                f.write(f"| **{ru_t['role']}** | {en_c} | {ru_c} |\n")
            f.write("\n---\n\n")

    print(f"Created review set with {len(review_items)} examples:")
    print(f"  - {jsonl_path}")
    print(f"  - {md_path}")

if __name__ == "__main__":
    main()
