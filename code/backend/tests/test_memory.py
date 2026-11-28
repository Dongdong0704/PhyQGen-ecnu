"""Regression coverage for the scope and lifecycle of generation memory."""

import sqlite3
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import accounts
import questions
import storage
from agents.memory import load_prompt_memory


PARAMS = {
    "grade": "高一",
    "knowledge_point": "牛顿第二定律",
    "question_type": "short_answer",
    "require_illustration": False,
    "use_kb": True,
}


class GenerationMemoryTests(TestCase):
    def setUp(self):
        resources = ExitStack()
        self.addCleanup(resources.close)
        data_dir = Path(resources.enter_context(TemporaryDirectory()))
        resources.enter_context(patch.object(storage, "DATA_DIR", data_dir))
        storage.initialize()
        with storage.db(write=True) as conn:
            self.teacher = accounts.add_user(conn, "memory-owner", "", "test-password", "TEACHER")
            self.other = accounts.add_user(conn, "other-teacher", "", "test-password", "TEACHER")

    def save_question(self, title, task_id, *, teacher=None, task_exists=True, **fields):
        teacher = teacher or self.teacher
        owner = teacher["id"]
        created_at = storage.now()
        question = {
            **PARAMS,
            "user_id": owner,
            "task_id": task_id,
            "title": title,
            "content": "根据合力计算小车的加速度。",
            "options": None,
            "answer": "2 m/s²",
            "explanation": "先求物体所受的合力，再用牛顿第二定律计算加速度。",
            "illustration_url": None,
            "created_at": created_at,
            "updated_at": created_at,
            "teacher_status": "pending",
            "version": 1,
            "confirmations": [],
            "rating": 5,
            "comment": "仅供教师查看的备注",
            **fields,
        }
        question["versions"] = [questions.version_snapshot(question, "system")]
        with storage.db(write=True) as conn:
            question_id = questions.insert_question(conn, question)["id"]
            if task_exists:
                task = {
                    "id": task_id,
                    "user_id": owner,
                    "params": {key: question[key] for key in PARAMS},
                    "items": [{"index": 1, "status": "draft", "question_id": question_id}],
                    "completed": True,
                }
                conn.execute(
                    "INSERT INTO tasks (id, user_id, created_at, completed, payload) VALUES (?, ?, ?, 1, ?)",
                    (task_id, owner, created_at, storage.encode(task)),
                )
        return question_id

    def recall(self, **params):
        return load_prompt_memory(self.teacher["id"], "current-batch", {**PARAMS, **params})

    def test_episodes_prioritize_current_batch_and_stay_within_teacher_grade_and_topic(self):
        self.save_question("本批小车题", "current-batch")
        self.save_question("旧批斜面题", "previous-batch")
        self.save_question("其他年级", "another-grade", grade="高二")
        self.save_question("相似但不同的知识点", "another-topic", knowledge_point="牛顿第二定律与第三定律")
        other_id = self.save_question("其他教师", "other-batch", teacher=self.other)
        questions.confirm_question(other_id, questions.Revision(version=1), self.other)

        memories = self.recall()
        self.assertEqual([entry["标题"] for entry in memories["episodes"]], ["本批小车题", "旧批斜面题"])
        self.assertEqual(memories["examples"], [])
        self.assertEqual(
            self.recall(use_kb=False),
            {"episodes": [{"标题": "本批小车题", "题干节选": "根据合力计算小车的加速度。"}], "examples": []},
        )

    def test_examples_follow_teacher_confirmation_and_question_lifecycle(self):
        question_id = self.save_question("小车原稿", "previous-batch")
        self.assertEqual(self.recall()["examples"], [])

        questions.confirm_question(question_id, questions.Revision(version=1), self.teacher)
        self.assertEqual([entry["标题"] for entry in self.recall()["examples"]], ["小车原稿"])
        self.assertEqual(self.recall(use_kb=False)["examples"], [])

        questions.edit_question(
            question_id,
            questions.DraftPatch(
                version=1,
                title="教师修订稿",
                content="根据两个相反方向的力求加速度。",
                answer="1 m/s²",
                explanation="先选正方向，再计算合力。",
            ),
            self.teacher,
        )
        memories = self.recall()
        self.assertEqual([entry["标题"] for entry in memories["episodes"]], ["小车原稿"])
        self.assertEqual(memories["examples"], [])

        questions.confirm_question(question_id, questions.Revision(version=2), self.teacher)
        self.assertEqual(
            self.recall()["examples"],
            [{"标题": "教师修订稿", "题干节选": "根据两个相反方向的力求加速度。", "解析节选": "先选正方向，再计算合力。"}],
        )
        questions.delete_question(question_id, self.teacher)
        self.assertEqual(self.recall(), {"episodes": [], "examples": []})

    def test_examples_require_a_matching_generated_question_and_send_only_bounded_excerpts(self):
        fixture_id = self.save_question("演示题", "DEMO-INITIAL", task_exists=False)
        wrong_type_id = self.save_question("填空题", "different-type", question_type="fill_blank")
        self.save_question(
            "当前版本未确认", "stale-version", teacher_status="confirmed", version=2,
            confirmations=[{"version": 1, "teacher_id": self.teacher["id"]}],
        )
        self.save_question(
            "当前版本由另一人确认", "another-reviewer", teacher_status="confirmed",
            confirmations=[{"version": 1, "teacher_id": self.other["id"]}],
        )
        draft_id = self.save_question(
            "真实习题", "actual-batch",
            content="小车受力后运动。" + "甲" * 1500 + "题干末尾",
            explanation="先写合力方向。" + "乙" * 1500 + "解析末尾",
        )
        for question_id in (fixture_id, wrong_type_id, draft_id):
            questions.confirm_question(question_id, questions.Revision(version=1), self.teacher)

        examples = self.recall()["examples"]
        self.assertEqual([entry["标题"] for entry in examples], ["真实习题"])
        self.assertEqual(set(examples[0]), {"标题", "题干节选", "解析节选"})
        self.assertTrue(examples[0]["题干节选"].startswith("小车受力后运动。"))
        self.assertTrue(examples[0]["解析节选"].startswith("先写合力方向。"))
        self.assertNotIn("题干末尾", examples[0]["题干节选"])
        self.assertNotIn("解析末尾", examples[0]["解析节选"])

    def test_recalls_only_a_few_recent_entries(self):
        for index in range(6):
            question_id = self.save_question(f"受力情境 {index}", f"batch-{index}")
            questions.confirm_question(question_id, questions.Revision(version=1), self.teacher)

        memories = self.recall()
        self.assertEqual(
            [entry["标题"] for entry in memories["episodes"]],
            ["受力情境 5", "受力情境 4", "受力情境 3", "受力情境 2"],
        )
        self.assertEqual([entry["标题"] for entry in memories["examples"]], ["受力情境 5", "受力情境 4"])

    def test_read_failure_returns_empty_memory(self):
        with patch("agents.memory.db", side_effect=sqlite3.OperationalError("read failed")):
            with self.assertLogs("agents.memory", level="WARNING"):
                self.assertEqual(self.recall(), {"episodes": [], "examples": []})
