"""
Russian judge prompts, category definitions, and prompt generation utility for NC-Bench-RU.
Maintains exact label compatibility with upstream IBM NC-Bench while providing
functionally equivalent, native Russian instructions for evaluating LLM responses.
"""
import json

sys_prompt_ru = '''Ты — классификационная модель, способная понимать естественный язык, коммуникативные намерения и структуру разговорных паттернов. Твоя роль — классификатор диалоговых реплик. Ты должен строго следовать всем приведённым ниже инструкциям, основываясь только на предоставленных данных и никакой иной информации.'''

judge_prompt_ru = '''Предоставляется фрагмент диалога между [USER] (пользователем) и [AGENT] (агентом). Классифицируй последнюю реплику [AGENT], которая может состоять из одного или нескольких предложений.

Диалог:
<transcript_with_turn_num>

Метки классификации:
<labels>

Правила, которым ты ОБЯЗАН следовать:

1. Твоя задача — классифицировать предложения реплики [AGENT] в последней реплике. НИКОГДА не классифицируй реплики [USER].

2. Если ответ [AGENT] содержит несколько предложений, ты должен классифицировать каждое предложение. Если предложений несколько, раздели метки классов запятыми.

3. Если последняя реплика [AGENT] пустая или состоит только из пробелов, ты обязан классифицировать её как Silence.

4. Ты должен игнорировать паузы.

5. Отвечай только меткой класса или метками классов через запятую. Не включай никаких объяснений или цитат.

Классифицируй строку <last_agent_turn_num> реплики [AGENT], используя предоставленные метки.'''

def_inquiry_ru = '''
- Answer: Предпочтительный ответ на вопрос, запрос или просьбу, предоставляющий запрашиваемую информацию, выполняющий запрос или дающий рекомендацию; например, указание часов работы в ответ на вопрос о времени работы пекарни, закрытие счёта или рекомендация отеля.
- NonAnswer: Неспособность или отказ предоставить ответ на запрос или выполнить действие, с объяснением причины или прямым отказом; например, «Боюсь, я не могу закрыть ваш счёт», «У нас нет моделей, соответствующих вашим предпочтениям» или «Извините, я не знаю ответа на ваш вопрос».
- RepeatRequest: Просьба к собеседнику повторить полностью или частично то, что он сказал ранее, для устранения проблемы со слышимостью; например, «что вы сказали?», «повторите» или «я вас не расслышал».
- ParaphraseRequest: Просьба к собеседнику переформулировать полностью или частично то, что он сказал ранее, не меняя смысла, для устранения проблемы с пониманием; например, «что вы имеете в виду?», «я не понимаю» или «можете сказать иначе?».
- DefinitionRequest: Запрос значения слова или фразы, ранее произнесённых собеседником, для устранения проблемы с пониманием; например, «что вы имеете в виду под взорвался», «что такое ДМС» или «что значит кето».
- ExampleRequest: Просьба привести конкретный пример общей идеи, выраженной в предыдущей реплике; например, «можете привести пример?» или «например, какой?».
- NewTopic: Смена темы разговора, предложение сменить тему, прекращение текущей темы или предложение альтернативного варианта действий; например, «давайте поговорим о другом», «кстати» или «с другой стороны».
- OOC: Высказывание не от лица роли AGENT, а от лица аналитика, ИИ-ассистента или мета-комментария; например, «(Примечание:», «В этом улучшенном диалоге», «Или вы могли бы сказать:» или рассуждения вслух (Chain-of-Thought).
- Other: Высказывание, не подходящее ни под один из вышеуказанных классов.
'''

def_repeat_ru = '''
- NonAnswer: Неспособность или отказ предоставить ответ на запрос или выполнить действие, с объяснением причины или прямым отказом; например, «Боюсь, я не могу закрыть ваш счёт», «У нас нет моделей, соответствующих вашим предпочтениям» или «Извините, я не знаю ответа на ваш вопрос».
- Repeat: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является повторением предыдущей реплики AGENT (<prior_turn>) теми же словами, например, для устранения проблемы USER со слышимостью. Это может быть полный или частичный повтор нерасслышанной реплики.
- Paraphrase: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является перефразированием предыдущей реплики AGENT (<prior_turn>) другими словами, например, для устранения проблемы USER с пониманием. Это может быть полный или частичный перефраз непонятой реплики.
- Definition: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является определением ключевого слова или фразы из предыдущей реплики AGENT (<prior_turn>), например, для устранения проблемы USER с пониманием этого термина. Например: «искусственный интеллект — это технология...» или «Шантийи — это вид взбитых сливок...».
- Example: Когда последняя реплика AGENT (строка <last_agent_turn_num>) приводит пример ключевого слова или фразы из предыдущей реплики AGENT (<prior_turn>), например, для устранения проблемы USER с пониманием. Например: «Олд Фешн — пример классического коктейля».
- OOC: Высказывание не от лица роли AGENT, а от лица аналитика, ИИ-ассистента или мета-комментария; например, «(Примечание:», «В этом улучшенном диалоге», «Или вы могли бы сказать:» или рассуждения вслух (Chain-of-Thought).
- Other: Высказывание, не подходящее ни под один из вышеуказанных классов.
'''

def_para_ru = def_repeat_ru
def_def_ru = def_repeat_ru
def_example_ru = def_repeat_ru

def_closer_ru = '''
- Answer: Предпочтительный ответ на вопрос, запрос или просьбу, предоставляющий запрашиваемую информацию, выполняющий запрос или дающий рекомендацию; например, указание часов работы в ответ на вопрос о времени работы пекарни, закрытие счёта или рекомендация отеля.
- NonAnswer: Неспособность или отказ предоставить ответ на запрос или выполнить действие, с объяснением причины или прямым отказом; например, «Боюсь, я не могу закрыть ваш счёт», «У нас нет моделей, соответствующих вашим предпочтениям» или «Извините, я не знаю ответа на ваш вопрос».
- Repeat: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является повторением предыдущей реплики AGENT (<prior_turn>) теми же словами, например, для устранения проблемы USER со слышимостью.
- Paraphrase: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является перефразированием предыдущей реплики AGENT (<prior_turn>) другими словами, например, для устранения проблемы USER с пониманием.
- Definition: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является определением ключевого слова или фразы из предыдущей реплики AGENT (<prior_turn>).
- Example: Когда последняя реплика AGENT (строка <last_agent_turn_num>) приводит пример ключевого слова или фразы из предыдущей реплики AGENT (<prior_turn>).
- Acknowledgment: Простое подтверждение того, что слова собеседника услышаны или поняты; например: «хорошо», «понятно», «ясно», «принято», «ага», «знаю».
- Appreciation: Выражение благодарности за то, что собеседник сказал или сделал; например: «спасибо» или «очень признателен».
- GratitudeReceipt: Ответная вежливая реплика на благодарность; например: «пожалуйста», «не за что», «на здоровье».
- Assessment: Оценка чего-либо как хорошего/плохого, позитивного/негативного; например: «отлично», «здорово», «супер», «класс», «ого», «жаль», «как плохо».
- PreClosing: Сигнал к завершению текущей темы или диалога в целом. Это может быть намерение уйти, ссылка на будущие контакты или проверка, остались ли ещё вопросы; например: «что-нибудь ещё?», «мне пора идти» или «это всё?».
- Apology: Выражение сожаления о причинённом неудобстве, ошибке или огорчении; например: «прошу прощения», «извините» или «сожалею».
- SequenceAbort: Сигнал об отмене или отзыве сказанного ранее, указывающий, что это больше не актуально и ответ больше не требуется; например: «неважно», «забудьте», «отбой».
- Silence: Пустой ответ или обозначение молчания/паузы; например: 'AGENT:   ', 'AGENT: (молчание)', 'AGENT: .......', 'AGENT:\n\n', 'AGENT: [empty]'.
- NewTopic: Смена темы разговора, предложение сменить тему или альтернативный вариант действий; например: «давайте поговорим о другом», «кстати».
- NonVerbal: Обозначение невербального действия, мимики или жеста словами или эмодзи; например, ((улыбается)), ((кивает)), ;) .
- OOC: Высказывание не от лица роли AGENT, а от лица аналитика, ИИ-ассистента или мета-комментария; например, «(Примечание:», Chain-of-Thought.
- Other: Высказывание, не подходящее ни под один из вышеуказанных классов.
'''

def_abort_ru = def_closer_ru
def_correction_ru = def_inquiry_ru

def_correction_open_request_ru = '''
- Answer: Предпочтительный ответ на вопрос, запрос или просьбу, предоставляющий запрашиваемую информацию, выполняющий запрос или дающий рекомендацию; например, указание часов работы в ответ на вопрос о времени работы пекарни, закрытие счёта или рекомендация отеля.
- NonAnswer: Неспособность или отказ предоставить ответ на запрос или выполнить действие, с объяснением причины или прямым отказом; например, «Боюсь, я не могу закрыть ваш счёт», «У нас нет моделей, соответствующих вашим предпочтениям» или «Извините, я не знаю ответа на ваш вопрос».
- DetailRequestGrounded: Запрос дополнительной информации, необходимой для выполнения запроса или ответа на вопрос. AGENT сможет лучше выполнить запрос, если узнает ключевые детали. Запрос деталей считается заземлённым (grounded), если он касается одной из этих конкретных деталей: <request_details>.
- DetailRequestUngrounded: Запрос любых других деталей, не указанных в DetailRequestGrounded.
- RepeatRequest: Просьба к собеседнику повторить полностью или частично то, что он сказал ранее, для устранения проблемы со слышимостью; например, «что вы сказали?», «повторите» или «я вас не расслышал».
- ParaphraseRequest: Просьба к собеседнику переформулировать то, что он сказал ранее, без изменения смысла, для устранения проблемы с пониманием; например, «что вы имеете в виду?», «я не понимаю».
- DefinitionRequest: Запрос значения слова или фразы, ранее произнесённых собеседником; например, «что вы имеете в виду под...», «что такое...».
- ExampleRequest: Просьба привести пример общей идеи, выраженной в предыдущей реплике; например, «можете привести пример?» или «например, какой?».
- NewTopic: Смена темы разговора, предложение сменить тему или прекращение текущей темы; например, «давайте о другом», «кстати».
- OOC: Высказывание не от лица роли AGENT, а от лица аналитика, ИИ-ассистента или мета-комментария; например, «(Примечание:», Chain-of-Thought.
- Other: Высказывание, не подходящее ни под один из вышеуказанных классов.
'''

def_repeat_open_request_ru = def_repeat_ru
def_repair_open_request_ru = def_repeat_ru
def_closer_open_request_ru = def_closer_ru

def_preliminary_open_request_ru = '''
- Affirmation: Положительный ответ на общий вопрос (да/нет) со стороны USER; например: «да», «конечно», «ага» или любые эквивалентные утвердительные слова.
- Acknowledgment: Простое подтверждение того, что слова собеседника услышаны или поняты; например: «хорошо», «понятно», «ясно», «принято», «ага», «знаю».
- Assessment: Оценка чего-либо как хорошего/плохого, позитивного/негативного; например: «отлично», «здорово», «супер», «класс», «ого», «жаль», «как плохо».
- HelpOffer: Предложение помощи USER вообще или с конкретным типом запроса; например: «чем могу вам помочь?», «я могу помочь вам с этим» или «хотите, я уточню информацию?».
- DetailRequestGrounded: Запрос дополнительной информации, необходимой для выполнения запроса или ответа на вопрос. AGENT сможет лучше выполнить запрос, если узнает ключевые детали. Запрос деталей считается заземлённым (grounded), если он касается одной из этих конкретных деталей: <request_details>.
- DetailRequestUngrounded: Запрос любых других деталей, не указанных в DetailRequestGrounded.
- OOC: Высказывание не от лица роли AGENT, а от лица аналитика, ИИ-ассистента или мета-комментария; например, «(Примечание:», Chain-of-Thought.
- Other: Высказывание, не подходящее ни под один из вышеуказанных классов.
'''

def_expansion_open_request_ru = '''
- Repeat: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является повторением предыдущей реплики AGENT (<prior_turn>) теми же словами, например, для устранения проблемы USER со слышимостью.
- Paraphrase: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является перефразированием предыдущей реплики AGENT (<prior_turn>) другими словами, например, для устранения проблемы USER с пониманием.
- Example: Когда последняя реплика AGENT (строка <last_agent_turn_num>) приводит пример ключевого слова или фразы из предыдущей реплики AGENT (<prior_turn>).
- Definition: Когда последняя реплика AGENT (строка <last_agent_turn_num>) является определением ключевого слова или фразы из предыдущей реплики AGENT (<prior_turn>).
- ChoiceGiving: Предоставление вариантов выбора USER для ответа на запрос деталей; например: «У нас есть маленькие, средние и большие стаканы» или «Мы продаём газовые, угольные и дровяные грили».
- OOC: Высказывание не от лица роли AGENT, а от лица аналитика, ИИ-ассистента или мета-комментария; например, «(Примечание:», Chain-of-Thought.
- Other: Высказывание, не подходящее ни под один из вышеуказанных классов.
'''


def generate_judge_prompts_ru(prompts_file, generations_file, language='ru', truncate_first_line=False, include_missing=True):
    """
    Generate evaluation prompts for judge LLM.
    Supports language='ru' (Russian instructions & definitions) and language='en' (original).
    Fixes upstream bugs:
      1. Falls back to chat_entry['request_details'] so grounded slot details are never blanked out.
      2. Preserves the full agent response (not just line 1) unless truncate_first_line=True.
      3. Handles omitted/missing tasks so models that fail or drop tasks receive score 0 instead of being ignored.
    """
    from utils import (
        sys_prompt as sys_prompt_en,
        judge_prompt as judge_prompt_en,
        def_inquiry as def_inquiry_en,
        def_repeat as def_repeat_en,
        def_para as def_para_en,
        def_def as def_def_en,
        def_example as def_example_en,
        def_closer as def_closer_en,
        def_abort as def_abort_en,
        def_correction as def_correction_en,
        def_correction_open_request as def_correction_open_request_en,
        def_repeat_open_request as def_repeat_open_request_en,
        def_repair_open_request as def_repair_open_request_en,
        def_closer_open_request as def_closer_open_request_en,
        def_preliminary_open_request as def_preliminary_open_request_en,
        def_expansion_open_request as def_expansion_open_request_en,
    )

    is_ru = (language == 'ru')
    cur_sys_prompt = sys_prompt_ru if is_ru else sys_prompt_en
    cur_judge_prompt = judge_prompt_ru if is_ru else judge_prompt_en

    # Read chat prompts
    with open(prompts_file, 'r', encoding='utf-8') as f:
        chat_data = {json.loads(line)['id']: json.loads(line) for line in f}

    # Read model generations
    with open(generations_file, 'r', encoding='utf-8') as f:
        response_data = {json.loads(line)['id']: json.loads(line) for line in f}

    combined_data = []
    for task_id, chat_entry in chat_data.items():
        if task_id in response_data:
            response_entry = response_data[task_id]
            is_missing = False
        else:
            if not include_missing:
                continue
            # Missing output: model did not generate an answer for this prompt
            response_entry = {
                'id': task_id,
                'task': chat_entry['task'],
                'output': '[empty]',
            }
            is_missing = True

        task_description = response_entry.get('task') or chat_entry.get('task')

        # Bug fix: check response_entry first, then fall back to chat_entry
        request_details = response_entry.get('request_details') or chat_entry.get('request_details', '')

        if is_ru:
            if task_description in ('inquiry', 'incremental request', 'inquiry ungrounded', 'incremental-self-correction'):
                label = def_inquiry_ru
            elif task_description == 'repeat request':
                label = def_repeat_ru
            elif task_description == 'paraphrase request':
                label = def_para_ru
            elif task_description == 'definition request':
                label = def_def_ru
            elif task_description == 'example request':
                label = def_example_ru
            elif task_description in ('sequence closer', 'sequence closer-acknowledgment (include)',
                                      'sequence closer-agreement (include)', 'sequence closer-appreciation (include)',
                                      'sequence closer-assessment (include)'):
                label = def_closer_ru
            elif task_description == 'sequence abort':
                label = def_abort_ru
            elif task_description == 'self-correction':
                label = def_correction_ru
            elif task_description in ('Self-Correction', 'Recommendation-Compact', 'Recommendation-Expanded', 'Recommendation-Incremental', 'Detail Request-Partial', 'Detail Request-All', 'Detail Request-Expanded'):
                label = def_correction_open_request_ru
            elif task_description in ('Repeat', 'Partial Repeat'):
                label = def_repeat_open_request_ru
            elif task_description in ('Paraphrase', 'Example', 'Definition'):
                label = def_repair_open_request_ru
            elif task_description in ('Closer', 'Abort'):
                label = def_closer_open_request_ru
            elif task_description in ('Preliminary-Screen', 'Preliminary-Detail'):
                label = def_preliminary_open_request_ru
            elif task_description in ('Expansion-Choices', 'Expansion-Repair'):
                label = def_expansion_open_request_ru
            else:
                raise RuntimeError(f"Unknown task description: {task_description}")
        else:
            if task_description in ('inquiry', 'incremental request', 'inquiry ungrounded', 'incremental-self-correction'):
                label = def_inquiry_en
            elif task_description == 'repeat request':
                label = def_repeat_en
            elif task_description == 'paraphrase request':
                label = def_para_en
            elif task_description == 'definition request':
                label = def_def_en
            elif task_description == 'example request':
                label = def_example_en
            elif task_description in ('sequence closer', 'sequence closer-acknowledgment (include)',
                                      'sequence closer-agreement (include)', 'sequence closer-appreciation (include)',
                                      'sequence closer-assessment (include)'):
                label = def_closer_en
            elif task_description == 'sequence abort':
                label = def_abort_en
            elif task_description == 'self-correction':
                label = def_correction_en
            elif task_description in ('Self-Correction', 'Recommendation-Compact', 'Recommendation-Expanded', 'Recommendation-Incremental', 'Detail Request-Partial', 'Detail Request-All', 'Detail Request-Expanded'):
                label = def_correction_open_request_en
            elif task_description in ('Repeat', 'Partial Repeat'):
                label = def_repeat_open_request_en
            elif task_description in ('Paraphrase', 'Example', 'Definition'):
                label = def_repair_open_request_en
            elif task_description in ('Closer', 'Abort'):
                label = def_closer_open_request_en
            elif task_description in ('Preliminary-Screen', 'Preliminary-Detail'):
                label = def_preliminary_open_request_en
            elif task_description in ('Expansion-Choices', 'Expansion-Repair'):
                label = def_expansion_open_request_en
            else:
                raise RuntimeError(f"Unknown task description: {task_description}")

        # Build transcript with turn numbers
        label_prompt_parts = []
        for i, message in enumerate(chat_entry['chat_prompt']):
            role = message['role']
            content = message['content']
            if role == "user":
                label_prompt_parts.append(f"{i} USER: {content}")
            elif role in ("assistant", "agent"):
                label_prompt_parts.append(f"{i} AGENT: {content}")

        # Model output formatting: evaluate full response by default, preserving all sentences
        raw_output = response_entry.get('output', '')
        if truncate_first_line:
            agent_turn_text = raw_output.split('\n')[0].strip() if raw_output else ''
        else:
            # Full response: clean and normalize internal line breaks so all sentences are evaluated
            agent_turn_text = " ".join([line.strip() for line in raw_output.splitlines() if line.strip()])

        if not agent_turn_text:
            agent_turn_text = "[empty]"

        label_prompt_parts.append(f"{i+1} AGENT: {agent_turn_text}")
        label_prompt = "\n".join(label_prompt_parts)

        prior_turn = ''
        if i - 1 >= 1:
            prior_turn = ('строка ' if is_ru else 'line ') + str(i - 1)

        judge_prompt_final = (
            cur_judge_prompt.replace("<labels>", label.strip())
            .replace("<last_agent_turn_num>", str(i + 1))
            .replace("<transcript_with_turn_num>", label_prompt)
            .replace("<prior_turn>", prior_turn)
            .replace("<request_details>", request_details)
        )

        combined_entry = {
            "id": task_id,
            "task": chat_entry["task"],
            "is_missing": is_missing,
            "chat_prompt": [
                {"role": "system", "content": cur_sys_prompt},
                {"role": "user", "content": judge_prompt_final}
            ]
        }
        combined_data.append(combined_entry)

    return combined_data

