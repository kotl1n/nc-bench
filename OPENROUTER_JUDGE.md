# Судья NC-Bench-RU через OpenRouter

Основной выбранный судья: **`meta/muse-spark-1.3-contributor`**.
Скрипт: `judge_openrouter.py`, endpoint `https://openrouter.ai/api/v1/chat/completions`.
Скрипт использует стандартную библиотеку Python; установка torch и локальная GPU для судьи не нужны.

Ключ берётся из переменной `OPENROUTER_API_KEY` или локального `.env.local` рядом со скриптом.
Переменная окружения имеет приоритет. Пример конфигурации без ключа: `.env.example`.
Файлы `.env` и `.env.*` исключены из Git, кроме `.env.example`. Локальному файлу с ключом следует установить права `600`.

## Проверка входов без обращения к API

```sh
python3 judge_openrouter.py \
  --prompts_file data_ru/conversation_competence_ru.jsonl \
  --generations_file outputs/generations/our500m_basic.jsonl \
  --judgments_file outputs/judgments/muse_spark_basic.jsonl \
  --dry-run
```

Нужны реальные генерации на всех ID выбранного набора. Пропущенные/дублированные/лишние ID
и несовпадения категорий блокируют запуск. Пустая строка в существующей генерации отличается
от отсутствующего задания. Генерации с известным обрезанием или ошибкой требуют отдельного разбора.

## Оценка через API

```sh
python3 judge_openrouter.py \
  --prompts_file data_ru/conversation_competence_ru.jsonl \
  --generations_file outputs/generations/our500m_basic.jsonl \
  --judgments_file outputs/judgments/muse_spark_basic.jsonl \
  --language ru --max_new_tokens 1024
```

Это оплачиваемые запросы к OpenRouter по тарифу модели. Публичный каталог проверен при настройке;
авторизованный inference и проверка ключа не выполнялись. Инструкции и ответы,
отправляемые судье, обрабатываются OpenRouter и провайдером выбранной модели.

Оценки сохраняются после каждого ответа с `fsync`. Для продолжения добавьте `--resume`:
совпадение входов, модели, языка, лимита и сформированных промптов проверяется по хешам.
Нормальные оценки пишутся в JSONL; настройки, полнота и состояние — в соседний `.jsonl.meta.json`.
Обрезанный/пустой ответ судьи и сетевые ошибки останавливают запуск с сохранением ранее полученных оценок.
Автоматических повторов запросов нет.

Публиковать итог можно только при `status=complete` и `completed_count=expected_count` в metadata.
Для RAG и Complex Request запускайте отдельные файлы результатов с соответствующим `--prompts_file`.

```sh
python3 aggregator_ru.py \
  --judgments_dir outputs/judgments \
  --evaluations_dir outputs/evaluations --mode strict
```

Судья оценивает разговорные действия. Надёжность именно Muse Spark на RU-адаптации ещё требует
проверки на человеческой разметке; результаты нельзя автоматически приравнивать к протоколу статьи IBM.
Скрипты GPT-4o и локальных судей остаются альтернативными backend-ами.
