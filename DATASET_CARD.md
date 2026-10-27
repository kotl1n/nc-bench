---
language:
- ru
- en
license: apache-2.0
tags:
- conversational-competence
- benchmark
- evaluation
- conversation-analysis
- dialogue
- llm-judge
size_categories:
- n<1K
dataset_info:
  features:
  - name: id
    dtype: int64
  - name: original_id
    dtype: int64
  - name: ru_id
    dtype: string
  - name: task
    dtype: string
  - name: chat_prompt
    list:
    - name: role
      dtype: string
    - name: content
      dtype: string
  - name: assistant_role
    dtype: string
  - name: user_role
    dtype: string
  - name: request_type
    dtype: string
  - name: request_details
    dtype: string
  splits:
  - name: basic
    num_bytes: 115531
    num_examples: 180
  - name: rag
    num_bytes: 331204
    num_examples: 180
  - name: complex_request
    num_bytes: 375037
    num_examples: 360
---

# NC-Bench-RU: Неофициальная русскоязычная адаптация бенчмарка разговорной компетентности IBM NC-Bench

> **Важное уведомление**: Данный проект является **неофициальной исследовательской адаптацией** датасета и методологии [IBM NC-Bench](https://github.com/IBM/nc-bench) на русский язык. Проект не является официальным продуктом IBM Research и не аффилирован с авторами оригинальной статьи.

- **Оригинальная статья**: [NC-Bench: An LLM Benchmark for Evaluating Conversational Competence](https://arxiv.org/abs/2601.06426v3) (Moore et al., arXiv:2601.06426v3, 2026).
- **Исходный англоязычный датасет**: [ibm-research/nc-bench](https://huggingface.co/datasets/ibm-research/nc-bench) (Revision: `af164c5d5999ecbc899d558cdd855d357d5656a6`).
- **Исходный код IBM**: [IBM/nc-bench](https://github.com/IBM/nc-bench) (Commit: `487225a9704cd3bf84e87592da0735161402f1c8`).
- **Текущий статус релиза**: `draft/unvalidated` (пройдена двухпроходная автоматическая верификация; ожидает независимого человеческого ревью).

---

## Описание датасета

**NC-Bench-RU** — независимый бенчмарк для проверки **разговорной компетентности** (Conversational Competence) русскоязычных языковых моделей, включая компактные модели класса ~500M параметров.

В отличие от традиционных бенчмарков фактологических знаний (MMLU) или следования инструкциям (IFEval), NC-Bench проверяет способность модели вести живой диалог в соответствии с законами **конверсационного анализа (Conversation Analysis)**:
- Различать просьбу повторить (сбой слышимости) и просьбу объяснить (сбой понимания);
- Корректно завершать разговор при репликах завершения («Понял», «Спасибо», «Ясно»), а не навязывать новые вопросы;
- Мгновенно отменять действие при репликах отмены («Неважно», «Отбой»);
- Задавать заземлённые вопросы для выяснения недостающих деталей при неполных запросах (Slot Elicitation);
- Корректно реагировать на самоисправления пользователя с сохранением контекстной неоднозначности.

---

## Состав и структура датасета

Датасет содержит ровно **720 заданий**, разделённых на 3 подмножества:

| Подмножество | Количество заданий | Категорий | Примеров на категорию | Описание |
| :--- | :---: | :---: | :---: | :--- |
| **Basic** | 180 | 9 | 20 | Базовые бытовые диалоги (просьба повторить, перефразировать, определение, пример, завершение, отмена, самоисправление, базовый запрос). |
| **RAG** | 180 | 9 | 20 | Диалоги с опорой на контекстный документ (27 уникальных текстов). Проверяет также способность давать `NonAnswer` на вопросы без ответа в тексте (`inquiry ungrounded`). |
| **Complex Request** | 360 | 18 | 20 персон | Ролевые многоэтапные сценарии (20 профессиональных ролей: бариста, консьерж, врач, автомеханик и др. × 18 коммуникативных действий). |
| **ИТОГО** | **720** | **36** | — | **Полная симметрия с англоязычным оригиналом.** |

### Схема данных (JSONL)

Каждая запись содержит:
- `id` (int): Исходный числовой ID (0..179 в Basic/RAG, 0..359 в Complex Request).
- `original_id` (int): Ссылка на ID в оригинальном англоязычном датасете IBM.
- `ru_id` (string): Уникальный строковый идентификатор адаптации (`basic_000`..`basic_179`, `rag_000`..`rag_179`, `complex_000`..`complex_359`).
- `task` (string): Категория диалогового действия (сохранено оригинальное машинное название для совместимости).
- `chat_prompt` (list): История диалога в формате `[{'role': 'user'/'assistant'/'system', 'content': '...'}]`.
- Для Complex Request дополнительно присутствуют поля метаданных:
  - `assistant_role` (string): Профессиональная роль ассистента на русском языке.
  - `user_role` (string): Роль собеседника.
  - `request_type` (string): Предмет запроса.
  - `request_details` (string): Список обязательных для выяснения слотов/деталей.

---

## Инструкции по использованию

### 1. Загрузка через Hugging Face Datasets

```python
from datasets import load_dataset

# Загрузка локальных файлов или после публикации в Hub:
dataset_basic = load_dataset("json", data_files="data_ru/basic/basic.jsonl")["train"]
dataset_rag = load_dataset("json", data_files="data_ru/rag/rag.jsonl")["train"]
dataset_complex = load_dataset("json", data_files="data_ru/complex_request/complex_request.jsonl")["train"]
```

### 2. Строгое предназначение: Только оценка (Evaluation Only)

> [!CAUTION]
> **Бенчмарк предназначен исключительно для тестирования и валидации моделей.**
> Категорически запрещается:
> - Использовать задания датасета для обучения, дообучения (SFT), RLHF или создания синтетических ответов.
> - Смешивать датасет с обучающими корпусами.
> - Прямо приравнивать баллы RU и EN без проведения кросс-языковой калибровки судей.

---

## Лицензия и цитирование

Датасет распространяется на условиях лицензии **Apache 2.0** в соответствии с лицензией оригинального репозитория IBM NC-Bench.

При использовании русскоязычной адаптации, пожалуйста, цитируйте оригинальную статью:

```bibtex
@article{moore2026ncbench,
  title={NC-Bench: An LLM Benchmark for Evaluating Conversational Competence},
  author={Moore, Robert J. and others},
  journal={arXiv preprint arXiv:2601.06426v3},
  year={2026}
}
```
