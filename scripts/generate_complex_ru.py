#!/usr/bin/env python3
"""
Complete generator for Russian adaptation of NC-Bench Complex Request set (360 items).
Preserves original IDs, 20 personas, 18 conversational tasks per persona,
conversational action criteria, and grounded slot elicitation logic.
"""
import json
import os

with open("nc-bench/scripts/complex_personas.json", "r", encoding="utf-8") as f:
    ORIG_PERSONAS = json.load(f)

# Persona metadata translations
PERSONA_META_RU = {
    0: {
        "assistant_role": "консьерж в отеле",
        "user_role": "Гости",
        "request_type": "рекомендации ресторанов",
        "request_details": "какую кухню они хотят и как далеко от отеля готовы отправиться",
    },
    1: {
        "assistant_role": "бариста",
        "user_role": "Клиенты",
        "request_type": "кофе",
        "request_details": "какой объём напитка они хотят, нужен ли им эспрессо или фильтр-кофе, какое молоко добавить (если нужно) и какой подсластитель добавить (если нужно)",
    },
    2: {
        "assistant_role": "продавец-консультант",
        "user_role": "Покупатель",
        "request_type": "смартфон",
        "request_details": "какой бренд они хотят, ищут ли флагманскую модель, самую бюджетную или среднебюджетную, и какой экран они предпочитают — побольше или поменьше",
    },
    3: {
        "assistant_role": "специалист технической поддержки",
        "user_role": "Пользователь",
        "request_type": "компьютерную помощь",
        "request_details": "могут ли они открыть крупный сайт, например google.com, включён ли Wi-Fi на компьютере, перезагружали ли они роутер или модем",
    },
    4: {
        "assistant_role": "турагент",
        "user_role": "Клиент",
        "request_type": "туристическую консультацию и бронирование",
        "request_details": "какую страну или континент они рассматривают, какую погоду предпочитают и чем любят заниматься в отпуске",
    },
    5: {
        "assistant_role": "репетитор",
        "user_role": "Ученик",
        "request_type": "помощь по математике",
        "request_details": "какой предмет по математике они изучают, какую оценку получают и по каким конкретным темам им нужна помощь",
    },
    6: {
        "assistant_role": "психотерапевт",
        "user_role": "Пациент",
        "request_type": "психотерапевтическую помощь",
        "request_details": "произошло ли что-то, что могло вызвать тревогу, насколько сильна тревога и что именно её провоцирует",
    },
    7: {
        "assistant_role": "подрядчик по ремонту",
        "user_role": "Владелец дома",
        "request_type": "ремонт кухни",
        "request_details": "из какого материала они хотят столешницу, хотят ли они накладную или подстольную мойку и нужен ли им кухонный фартук",
    },
    8: {
        "assistant_role": "свадебный организатор",
        "user_role": "Молодожёны",
        "request_type": "место для церемонии",
        "request_details": "в помещении или на открытом воздухе они хотят церемонию, какое время суток предпочитают (утро, день, вечер) и сколько гостей ожидается",
    },
    9: {
        "assistant_role": "графический дизайнер",
        "user_role": "Клиент",
        "request_type": "логотип для компании «Silver Bear Inc.»",
        "request_details": "знают ли они, какую форму логотипа хотят, нужно ли изображение медведя и хотят ли они полное название компании или аббревиатуру",
    },
    10: {
        "assistant_role": "финансовый консультант",
        "user_role": "Клиент",
        "request_type": "совет по пенсионным накоплениям",
        "request_details": "сколько сбережений у них есть сейчас, сколько у них долгов и есть ли у них пенсионный план 401(k) или пенсия",
    },
    11: {
        "assistant_role": "официант",
        "user_role": "Гость",
        "request_type": "блюда",
        "request_details": "хотят ли они услышать фирменные блюда дня, желают ли закуску и планируют ли десерт",
    },
    12: {
        "assistant_role": "HR-специалист",
        "user_role": "Сотрудник",
        "request_type": "информацию об отпуске",
        "request_details": "работает ли он на полную или неполную ставку, в какой стране работает и как давно работает в компании",
    },
    13: {
        "assistant_role": "риелтор",
        "user_role": "Покупатель",
        "request_type": "дом на продажу",
        "request_details": "ищут ли они таунхаус или отдельный дом, сколько спален им нужно и важен ли хороший школьный район",
    },
    14: {
        "assistant_role": "автомеханик",
        "user_role": "Автовладелец",
        "request_type": "ремонт автомобиля",
        "request_details": "в чём заключается проблема с машиной, как давно она возникла и какого года выпуска автомобиль",
    },
    15: {
        "assistant_role": "карьерный консультант",
        "user_role": "Соискатель",
        "request_type": "подготовку к собеседованиям",
        "request_details": "какую работу они ищут, какой уровень образования получили и какой у них релевантный опыт работы",
    },
    16: {
        "assistant_role": "банковский сотрудник",
        "user_role": "Клиент",
        "request_type": "открытие счёта",
        "request_details": "является ли он действующим клиентом банка, нужен ли личный или корпоративный счёт и хочет ли он открыть текущий счёт или сберегательный",
    },
    17: {
        "assistant_role": "представитель авиакомпании",
        "user_role": "Пассажир",
        "request_type": "авиабилеты",
        "request_details": "куда они хотят полететь, откуда вылетают, когда планируют поездку и сколько пассажиров будет в группе",
    },
    18: {
        "assistant_role": "продавец подержанных автомобилей",
        "user_role": "Покупатель",
        "request_type": "подержанный автомобиль",
        "request_details": "какой тип кузова они ищут (седан, кроссовер, компактный и т. д.), хотят ли бензиновый двигатель, электромобиль или гибрид, и какой у них бюджет",
    },
    19: {
        "assistant_role": "страховой агент",
        "user_role": "Клиент",
        "request_type": "страхование жизни",
        "request_details": "нужна ли им срочная или пожизненная страховка, кто будет выгодоприобретателем и какую сумму страхового покрытия они считают необходимой",
    },
}

def make_sys_prompt_ru(meta):
    return (
        f"Ты играешь роль: {meta['assistant_role']}. {meta['user_role']} будут просить у тебя {meta['request_type']}. "
        f"Когда они обращаются, выясни следующие обязательные детали: {meta['request_details']}. "
        f"Если {meta['user_role']} не сообщили эти детали, спроси о них. Задавай вопрос только об одной детали за раз. "
        f"Как только у тебя будет хотя бы немного информации по каждой детали, сделай рекомендацию или ответь на запрос. "
        f"Твои ответы должны быть длиной примерно в одно предложение или меньше."
    )

from complex_p0_p4 import TASKS_P0_P4
from complex_p5_p9 import TASKS_P5_P9
from complex_p10_p14 import TASKS_P10_P14
from complex_p15_p19 import TASKS_P15_P19

ALL_TASKS = {}
ALL_TASKS.update(TASKS_P0_P4)
ALL_TASKS.update(TASKS_P5_P9)
ALL_TASKS.update(TASKS_P10_P14)
ALL_TASKS.update(TASKS_P15_P19)

def main():
    with open("nc-bench/scripts/complex_en.json", "r", encoding="utf-8") as f:
        orig_items = json.load(f)
    
    out_items = []
    print(f"Total original complex items: {len(orig_items)}")
    
    for item in orig_items:
        item_id = item["id"]
        p_id = item_id % 20
        cat = item["task"]
        
        assert p_id in ALL_TASKS, f"Missing persona {p_id} in ALL_TASKS"
        assert cat in ALL_TASKS[p_id], f"Missing category {cat} in persona {p_id}"
        
        ru_turns = ALL_TASKS[p_id][cat]
        meta = PERSONA_META_RU[p_id]
        sys_prompt = make_sys_prompt_ru(meta)
        
        # Verify turn count match with original (excluding system prompt)
        orig_user_assistant_turns = [t for t in item["chat_prompt"] if t["role"] != "system"]
        assert len(ru_turns) == len(orig_user_assistant_turns), (
            f"Turn count mismatch at id={item_id} (p_id={p_id}, cat={cat}): "
            f"RU {len(ru_turns)} vs EN {len(orig_user_assistant_turns)}"
        )
        
        # Verify roles match
        for idx, (r, c) in enumerate(ru_turns):
            assert r == orig_user_assistant_turns[idx]["role"], (
                f"Role mismatch at id={item_id}, turn {idx}: {r} vs {orig_user_assistant_turns[idx]['role']}"
            )
        
        chat_prompt = [{"role": "system", "content": sys_prompt}]
        for r, c in ru_turns:
            chat_prompt.append({"role": r, "content": c})
            
        ru_entry = {
            "id": item_id,
            "original_id": item_id,
            "ru_id": f"complex_{item_id:03d}",
            "task": cat,
            "assistant_role": meta["assistant_role"],
            "user_role": meta["user_role"],
            "request_type": meta["request_type"],
            "request_details": meta["request_details"],
            "chat_prompt": chat_prompt
        }
        out_items.append(ru_entry)
        
    assert len(out_items) == 360, f"Expected 360 items, got {len(out_items)}"
    
    out_path = "nc-bench/data_ru/conversation_competence_open_request_ru.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for entry in out_items:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(out_items)} Complex Request RU items in {out_path}!")

if __name__ == "__main__":
    main()
