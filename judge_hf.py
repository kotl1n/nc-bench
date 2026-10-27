import argparse
import json
import os

import torch
import transformers
import datasets
from tqdm import tqdm

from utils import generate_judge_prompts


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--judge_path', type=str, required=True)
    parser.add_argument('--prompts_file', type=str, default='./data/conversation_competence.jsonl')
    parser.add_argument('--generations_file', type=str, required=True)
    parser.add_argument('--judgments_file', type=str, required=True)
    parser.add_argument('--max_new_tokens', default=128, type=int)
    parser.add_argument('--batch_size', default=4, type=int)
    parser.add_argument('--language', default='ru', choices=['ru', 'en'], help='Judge prompt language (ru or en)')
    args = parser.parse_args()
    return args


def main(args):
    if not os.path.isfile(args.prompts_file):
        print(f'prompts file does not exist: {args.prompts_file}')
        return

    if not os.path.isfile(args.generations_file):
        print(f'generations file does not exist: {args.generations_file}')
        return

    if os.path.isfile(args.judgments_file):
        print(f'judgments file already exists: {args.judgments_file}')
        return

    dir_name = os.path.dirname(args.judgments_file)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    # load model
    model = transformers.AutoModelForCausalLM.from_pretrained(
        args.judge_path,
        device_map='auto',
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    # load tokenizer
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.judge_path,
        padding_side='left',
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # load judge prompts
    judge_prompts = generate_judge_prompts(
        prompts_file=args.prompts_file,
        generations_file=args.generations_file,
        language=args.language,
    )
    dataset = datasets.Dataset.from_list(judge_prompts)

    # format input text and apply chat template
    def format_inputs(x):
        prompt = tokenizer.apply_chat_template(x['chat_prompt'], add_generation_prompt=True, tokenize=False)
        return {'prompt': prompt}
    formatted_dataset = dataset.map(format_inputs)

    # get model judgments
    model_outputs = []
    with tqdm(total=len(formatted_dataset)) as pbar:
        for batch in formatted_dataset.iter(batch_size=args.batch_size):
            prompts = batch['prompt']
            ids = batch['id']
            tasks = batch['task']

            # tokenize
            inputs = tokenizer(
                prompts,
                add_special_tokens=False,
                padding=True,
                truncation=False,
                return_token_type_ids=False,
                return_tensors='pt',
            ).to(model.device)

            # generate
            output = model.generate(
                **inputs,
                pad_token_id=tokenizer.pad_token_id,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                num_return_sequences=1,
            )
            preds = tokenizer.batch_decode(output[:, inputs['input_ids'].shape[1]:], skip_special_tokens=True)

            # store outputs
            for i in range(len(prompts)):
                model_output = {
                    'id': ids[i],
                    'task': tasks[i],
                    'output': preds[i],
                }
                model_outputs.append(model_output)

            pbar.update(len(prompts))

    # export model jugements to file
    with open(args.judgments_file, 'w', encoding='utf8') as f:
        for row in model_outputs:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    args = get_args()
    main(args)
