# NC-Bench-RU: Независимый бенчмарк разговорной компетентности русскоязычных языковых моделей
*(Неофициальная адаптация IBM NC-Bench)*

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Dataset](https://img.shields.io/badge/Dataset-720_tasks-green.svg)](#состав-датасета)
[![Status](https://img.shields.io/badge/Status-draft%2Funvalidated-orange.svg)](review/REVIEW_SET.md)

> [!IMPORTANT]
> **Статус проекта**: Неофициальная исследовательская адаптация. Не является официальным продуктом IBM.
> **Статус датасета**: `draft/unvalidated` — датасет прошёл полную двухпроходную программную верификацию структуры и семантики, но до завершения ручной разметки экспертами сохраняет статус предварительного черновика.

---

## 1. Введение и теоретическое обоснование

Большинство современных бенчмарков языковых моделей (MMLU, GSM8K, IFEval, Arena-Hard) оценивают модель как **информационный оракул** или **исполнитель разовых инструкций**. Однако в реальных диалоговых интерфейсах ключевую роль играет **разговорная компетентность (Conversational Competence)**.

Бенчмарк **NC-Bench** (Natural Conversation Benchmark), разработанный исследователями IBM Research (Moore et al., 2026), основан на фундаментальной лингвистической теории — **конверсационном анализе (Conversation Analysis, CA)**, сформулированном социологами Эмануэлем Щегловым (Emanuel Schegloff), Харви Саксом (Harvey Sacks) и Гейл Джефферсон (Gail Jefferson).

### В чём заключается разговорная компетентность?
В реальном разговоре реплики объединены в **соседские пары (adjacency pairs)**:
1. **Восстановление сбоев восприятия (Repair)**:
   - Если пользователь не расслышал реплику (*«Что вы сказали?»* / *RepeatRequest*), модель должна **повторить** сказанное дословно.
   - Если пользователь не понял смысл (*«Что вы имеете в виду?»* / *ParaphraseRequest*), модель обязана **перефразировать** свою мысль иными словами, а не повторять её заново.
   - Если пользователь переспрашивает термин (*«Что такое X?»* / *DefinitionRequest*), модель должна дать определение этого термина.
2. **Управление закрытием диалога (Pre-Closing & Sequence Closing)**:
   - Когда пользователь говорит «Понял», «Ясно», «Спасибо» или «Хорошо», он подаёт сигнал к завершению темы (*Sequence Closer*). Компетентная модель должна принять закрытие (ответить вежливостью, подтвердить закрытие или промолчать), а **не навязывать новую информацию или бесконечные встречные вопросы**.
3. **Отмена действия (Sequence Abort)**:
   - Реплики «Неважно», «Отбой», «Забудь» требуют немедленного прекращения действия и вежливого сворачивания ветки разговора.
4. **Выяснение параметров при неполных запросах (Slot Elicitation)**:
   - Если пользователь просит услугу («Порекомендуйте ресторан»), но не указал ключевые параметры, модель должна последовательно задавать **заземлённые вопросы только об одной детали за раз** (*DetailRequestGrounded*).
5. **Самоисправление пользователя (Self-Correction)**:
   - Способность быстро адаптироваться, если пользователь говорит «Нет, я имел в виду...», сохраняя контекст беседы.

---

## 2. Значение для небольших моделей (~500M параметров)

Малые модели (такие как SmolLM2-360M, Qwen2.5-0.5B, Vikhr-0.5B и другие) часто оптимизируются под формальное соответствие инструкциям. Из-за этого у них возникает типичный дефект: **гиперактивная генерация (over-generation)** и неспособность вовремя замолчать.
Тестирование на NC-Bench-RU позволяет выявить:
- Способна ли компактная модель понять сигнал отмены и промолчать (`Silence`);
- Отличает ли модель сбой слышимости от сбоя понимания;
- Не «забывает» ли модель о своей роли при многоэтапном уточнении деталей.

---

## 3. Состав датасета (720 заданий)

Все задания строго соответствуют англоязычному оригиналу IBM NC-Bench:

```
nc-bench/data_ru/
├── conversation_competence_ru.jsonl               # Basic (180 заданий)
├── conversation_competence_rag_ru.jsonl           # RAG (180 заданий)
├── conversation_competence_open_request_ru.jsonl  # Complex Request (360 заданий)
├── basic/basic.jsonl                              # Формат Hugging Face
├── rag/rag.jsonl                                  # Формат Hugging Face
└── complex_request/complex_request.jsonl          # Формат Hugging Face
```

### Подробное распределение:
1. **Basic (180 заданий, 9 категорий по 20 примеров)**:
   - `definition request`
   - `example request`
   - `incremental request`
   - `inquiry`
   - `paraphrase request`
   - `repeat request`
   - `self-correction`
   - `sequence abort`
   - `sequence closer`
2. **RAG (180 заданий, 9 категорий по 20 примеров, 27 контекстов)**:
   - Те же категории + `inquiry ungrounded` (проверка отказа отвечать на факты, отсутствующие в документе) и `incremental-self-correction`.
3. **Complex Request (360 заданий, 20 ролей × 18 коммуникативных действий)**:
   - Профессиональные роли: бариста, консьерж в отеле, автомеханик, продавец смартфонов, специалист техподдержки, турагент, репетитор, психотерапевт, подрядчик, свадебный организатор, графический дизайнер, финансовый консультант, официант, HR-специалист, риелтор, карьерный консультант, банковский сотрудник, представитель авиакомпании, продавец подержанных авто, страховой агент.

---

## 4. Воспроизводимый протокол запуска

### Шаг 1. Генерация ответов исследуемой моделью

```bash
# Для русскоязычной модели на Hugging Face (например, Qwen/Qwen2.5-0.5B-Instruct)
python3 pred_hf.py \
    --model_path Qwen/Qwen2.5-0.5B-Instruct \
    --prompts_file data_ru/conversation_competence_ru.jsonl \
    --generations_file outputs/generations/qwen05b_basic.jsonl \
    --max_new_tokens 1024 \
    --batch_size 8
```

> [!NOTE]
> В оригинальной статье IBM (Moore et al., 2026) используется протокол с **жадным декодированием (`do_sample=False`)** и лимитом в **1024 токена**.

### Шаг 2. Разметка ответов моделью-судьёй

Для оценки ответов используется LLM-судья с русскоязычными инструкциями (`--language ru`):

```bash
# Локальный судья на Hugging Face (например, Mistral-Large, Llama-3.3-70B или Qwen2.5-72B)
python3 judge_hf.py \
    --judge_path Qwen/Qwen2.5-72B-Instruct \
    --prompts_file data_ru/conversation_competence_ru.jsonl \
    --generations_file outputs/generations/qwen05b_basic.jsonl \
    --judgments_file outputs/judgments/qwen05b_basic_judge.jsonl \
    --language ru \
    --max_new_tokens 128 \
    --batch_size 4

# Либо через OpenAI API:
python3 judge_gpt4o.py \
    --judge gpt-4o-2024-08-06 \
    --prompts_file data_ru/conversation_competence_ru.jsonl \
    --generations_file outputs/generations/qwen05b_basic.jsonl \
    --judgments_file outputs/judgments/qwen05b_basic_judge.jsonl \
    --language ru
```

### Шаг 3. Агрегация результатов и подсчёт метрик

Мы предоставляем расширенный агрегатор `aggregator_ru.py`, поддерживающий два режима:

```bash
# Режим 1: Полная совместимость с upstream IBM NC-Bench
python3 aggregator_ru.py \
    --judgments_dir outputs/judgments/ \
    --evaluations_dir outputs/evaluations/ \
    --mode original

# Режим 2: Строгий/робастный режим (очистка пунктуации/markdown, учёт ошибок судьи, макро- и микро-усреднение)
python3 aggregator_ru.py \
    --judgments_dir outputs/judgments/ \
    --evaluations_dir outputs/evaluations/ \
    --mode strict
```

---

## 5. Дополнительная документация репозитория

- [DATASET_CARD.md](DATASET_CARD.md) — Карточка датасета в стандарте Hugging Face Hub.
- [ADAPTATION_LOG.md](ADAPTATION_LOG.md) — Подробный журнал решений, адаптации идиом и исправлений upstream-ошибок.
- [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) — Отчёт автоматической двухпроходной верификации всех 720 заданий.
- [review/REVIEW_SET.md](review/REVIEW_SET.md) — Выборка из 180 заданий (все категории + спорные случаи) для экспертного ручного ревью.
- [CHANGELOG.md](CHANGELOG.md) — Полная история изменений относительно оригинального репозитория IBM.
