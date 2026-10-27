# История изменений (CHANGELOG)

Все значимые изменения в проекте **NC-Bench-RU** (Неофициальная русскоязычная адаптация IBM NC-Bench) фиксируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

---

## [0.1.0-draft] — 2026-10-27

### Добавлено (Added)
- **Полная русскоязычная адаптация 720 диалоговых заданий**:
  - `data_ru/conversation_competence_ru.jsonl` (Basic: 180 заданий, 9 категорий по 20 примеров).
  - `data_ru/conversation_competence_rag_ru.jsonl` (RAG: 180 заданий, 9 категорий по 20 примеров, перевод 27 контекстных документов с сохранением фактов и числовых значений).
  - `data_ru/conversation_competence_open_request_ru.jsonl` (Complex Request: 360 заданий, 20 профессиональных ролей по 18 коммуникативных задач на роль).
- **Зеркало датасета в формате Hugging Face Datasets**:
  - `data_ru/basic/basic.jsonl`
  - `data_ru/rag/rag.jsonl`
  - `data_ru/complex_request/complex_request.jsonl`
- **Файлы соответствия идентификаторов (ID Mappings)**:
  - `mappings/id_map_basic.json`
  - `mappings/id_map_rag.json`
  - `mappings/id_map_complex_request.json`
- **Русскоязычные инструкции и определения категорий для модели-судьи**:
  - `utils_ru.py`: определения `sys_prompt_ru`, `judge_prompt_ru` и 14 словарей категорий на естественном русском языке при сохранении оригинальных машинных меток (`Answer`, `NonAnswer`, `Repeat`, `Paraphrase`, `Definition`, `Example`, `PreClosing`, `Silence`, `DetailRequestGrounded` и др.).
- **Универсальный скрипт агрегации результатов**:
  - `aggregator_ru.py`: поддержка двух режимов:
    - `--mode original` (100% совпадение с логикой upstream IBM `aggregator.py`);
    - `--mode strict` (очистка от маркдауна и пунктуации, выявление галлюцинированных меток судьи, расчёт macro- и micro-average).
- **Автоматизированная двухпроходная верификация**:
  - `scripts/verify_dataset.py`: проверка уникальности ID, схемы, порядка ролей, сохранности чисел, отрицаний и отсутствия непреднамеренных утечек английского текста.
  - `VERIFICATION_REPORT.md`: отчёт об успешном прохождении проверок.
- **Набор для независимого экспертного ручного ревью**:
  - `review/review_set.jsonl` и `review/REVIEW_SET.md` (180 заданий: минимум по 5 примеров на каждую из 36 категорий, все идиомы, сложные случаи).
  - Статус релиза явно помечен как `draft/unvalidated`.
- **Полная документация**:
  - `README_RU.md`: русскоязычное руководство по бенчмарку и тестированию малых моделей (~500M).
  - `ADAPTATION_LOG.md`: журнал адаптации идиом, реалий и исправления upstream-багов.
  - `DATASET_CARD.md`: карточка датасета для Hugging Face Hub.

### Исправлено в коде upstream (Fixed in Upstream Code)
- **Ошибка подстановки слотов судьи в `utils.py`**:
  - В оригинале `utils.generate_judge_prompts()` проверял поле `request_details` в `response_entry`, где его нет (оно сохраняется в `chat_entry`). В результате плейсхолдер `<request_details>` всегда заменялся на пустую строку `""`. Добавлен фоллбек `response_entry.get('request_details') or chat_entry.get('request_details', '')`.
- **Падение при флаге `--no_chat_template` в `pred_hf.py`**:
  - В оригинале скрипт обращался к несуществующему ключу `x['freeform_prompt']`. Реализована корректная сериализация `chat_prompt` в текстовый формат `User: ... / Assistant: ...`.
- **Сохранение метаданных в генерациях `pred_hf.py`**:
  - Добавлено сохранение поля `request_details` в `model_output`, если оно присутствует в исходных данных.
- **Исправление повреждённых символов (Mojibake) в RAG-контекстах**:
  - Контекст 23: `Comä»•ie-Franæº ise` исправлено на `Comédie-Française`.
  - Контекст 26: `Place VendÃ´me`, `CafÃ©` исправлено на `Place Vendôme`, `Café`.
- **Параметризация языка в судьях**:
  - В `judge_hf.py` и `judge_gpt4o.py` добавлен аргумент `--language ru/en` (по умолчанию `ru`).

### Известные особенности upstream (Documented Upstream Quirks)
- **Complex Request ID 340**: последняя реплика в оригинальном датасете IBM принадлежит `assistant` (вместо `user`). Сохранено bug-for-bug, задокументировано в журнале адаптации.
- **Пустые реплики пользователя в Basic (ID 1, 5, 6, 15, 85, 88)**: вызваны инициативой ассистента в начале диалога при требовании чередования `user -> assistant` в chat template. Сохранены.
