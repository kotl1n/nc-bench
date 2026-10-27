"""Offline controls for API routing, completeness, and durable resume. No API calls."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import judge_openrouter as judge


class JudgeOpenRouterTests(unittest.TestCase):
    def test_missing_extra_and_duplicate_ids(self):
        source = {0: {"task": "definition request"}}
        with self.assertRaises(ValueError):
            judge.validate_inputs(source, {})
        with self.assertRaises(ValueError):
            judge.validate_inputs(source, {0: {"task": "definition request", "output": ""}, 1: {}})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.jsonl"
            path.write_text('{"id":0}\n{"id":0}\n')
            with self.assertRaises(ValueError):
                judge.read_rows(path)

    def test_exact_openrouter_route_and_no_empty_or_truncated_judge(self):
        response = {"model": judge.DEFAULT_JUDGE, "choices": [{"message": {"content": "Definition"}, "finish_reason": "stop"}], "usage": {"total_tokens": 12}}
        with patch.object(judge.urllib.request, "urlopen", return_value=io.StringIO(json.dumps(response))) as call:
            result = judge.request_judgment([], judge.DEFAULT_JUDGE, "offline-dummy", 1024, 30)
            request = call.call_args.args[0]
            self.assertEqual(request.full_url, judge.ENDPOINT)
            self.assertEqual(json.loads(request.data)["model"], judge.DEFAULT_JUDGE)
            self.assertEqual(result["output"], "Definition")
        for content, reason in [("", "stop"), ("Definition", "length")]:
            response["choices"][0] = {"message": {"content": content}, "finish_reason": reason}
            with patch.object(judge.urllib.request, "urlopen", return_value=io.StringIO(json.dumps(response))):
                with self.assertRaises(RuntimeError):
                    judge.request_judgment([], judge.DEFAULT_JUDGE, "offline-dummy", 1024, 30)

    def test_checkpoint_resume_and_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            prompts = folder / "prompts.jsonl"
            generations = folder / "generations.jsonl"
            output = folder / "judge.jsonl"
            rows = [{"id": n, "task": "definition request", "chat_prompt": []} for n in range(2)]
            prompts.write_text("".join(json.dumps(row) + "\n" for row in rows))
            generations.write_text("".join(json.dumps({"id": row["id"], "task": row["task"], "output": "test"}) + "\n" for row in rows))
            args = argparse.Namespace(judge=None, prompts_file=str(prompts), generations_file=str(generations), judgments_file=str(output), language="ru", max_new_tokens=1024, timeout=30, dry_run=True, resume=False)
            config = {"OPENROUTER_API_KEY": "offline-dummy"}
            answer = {"output": "Definition", "finish_reason": "stop", "judge_model": judge.DEFAULT_JUDGE}
            with patch.object(judge, "build_judge_prompts", return_value=rows), patch.object(judge, "local_config", return_value=config), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(judge, "request_judgment") as api:
                    judge.run(args)
                    api.assert_not_called()
                    self.assertFalse(output.exists())
                args.dry_run = False
                with self.assertRaises(RuntimeError):
                    judge.run(args, transport=unittest.mock.Mock(side_effect=[answer, RuntimeError("offline interruption")]))
                self.assertEqual(len(judge.read_rows(output)), 1)
                args.resume = True
                resumed = unittest.mock.Mock(return_value=answer)
                metadata = judge.run(args, transport=resumed)
                self.assertEqual(resumed.call_count, 1)
                self.assertEqual(metadata["status"], "complete")
                self.assertEqual(metadata["completed_count"], 2)
                args.judge = "different-model"
                with self.assertRaises(ValueError):
                    judge.run(args, transport=resumed)

    def test_full_multiline_russian_response_is_visible(self):
        source = {0: {"task": "definition request", "chat_prompt": [
            {"role": "assistant", "content": "Это термин."},
            {"role": "user", "content": "Что он значит?"}]}}
        generations = {0: {"output": "Здравствуйте!\nSECOND_LINE_SENTINEL"}}
        prompts = judge.build_judge_prompts(source, generations, "ru")
        self.assertIn("SECOND_LINE_SENTINEL", prompts[0]["chat_prompt"][1]["content"])


if __name__ == "__main__":
    unittest.main()
