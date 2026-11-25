"""Regression coverage for public exercise data and threaded discussions."""

from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import accounts
import community
import questions
import storage


EXCELLENT = "/api/v1/excellent-questions"
DISCUSSIONS = "/api/v1/discussions"
QUESTIONS = "/api/v1/questions"


class CommunityTests(TestCase):
    def setUp(self):
        resources = ExitStack()
        self.addCleanup(resources.close)
        data_dir = Path(resources.enter_context(TemporaryDirectory()))
        resources.enter_context(patch.object(storage, "DATA_DIR", data_dir))
        storage.initialize()

        app = FastAPI()
        for router in (community.router, questions.router):
            app.include_router(router, prefix="/api")
        self.client = resources.enter_context(TestClient(app))
        self.owner_id, self.owner = self.create_account("owner")
        self.reader_id, self.reader = self.create_account("reader")

    def create_account(self, username, role="TEACHER"):
        with storage.db(write=True) as conn:
            user = accounts.add_user(conn, username, "", "test-password", role)
            token = accounts.start_session(conn, user)["data"]["access_token"]
        return user["id"], {"Authorization": f"Bearer {token}"}

    def create_question(
        self, title, *, rating=5, status="confirmed", version=1,
        confirmed_versions=(1,), created_at="2026-01-01T12:00:00+00:00",
        illustration_url=None,
    ):
        question = {
            "user_id": self.owner_id,
            "task_id": "PRIVATE-TASK-ID",
            "title": title,
            "content": "Apply Newton's laws to the object.",
            "question_type": "short_answer",
            "grade": "高一",
            "bloom_level": "apply",
            "difficulty": "中等",
            "knowledge_point": "牛顿第二定律",
            "options": None,
            "answer": "F = ma",
            "explanation": "Use the net force.",
            "illustration_url": illustration_url,
            "require_illustration": False,
            "created_at": created_at,
            "updated_at": created_at,
            "rating": rating,
            "comment": "PRIVATE COMMENT",
            "teacher_status": status,
            "version": version,
            "versions": [{"version": 1, "content": "PRIVATE DRAFT"}],
            "confirmations": [
                {
                    "version": number,
                    "teacher_id": self.owner_id,
                    "teacher_name": "owner",
                    "confirmed_at": created_at,
                }
                for number in confirmed_versions
            ],
            "evidence": [],
            "kb_reason": "未使用知识库",
        }
        with storage.db(write=True) as conn:
            return questions.insert_question(conn, question)["id"]

    def read_list(self, **params):
        response = self.client.get(f"{EXCELLENT}/list", headers=self.reader, params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def read_discussions(self, question_id, **params):
        response = self.client.get(
            f"{DISCUSSIONS}/list",
            headers=self.reader,
            params={"question_id": question_id, **params},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def post(self, question_id, headers, content="讨论内容", **fields):
        response = self.client.post(
            f"{DISCUSSIONS}/post",
            headers=headers,
            json={"question_id": question_id, "content": content, **fields},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def remove(self, discussion_id, headers, **fields):
        return self.client.request(
            "DELETE", f"{DISCUSSIONS}/delete", headers=headers,
            json={"discussion_id": discussion_id, **fields},
        )

    def test_only_current_confirmed_high_scores_are_public(self):
        public = self.create_question(
            "优秀习题", rating=4, version=2, confirmed_versions=(1, 2),
            illustration_url="/illustrations/newton.svg",
        )
        hidden = [
            self.create_question("三分", rating=3),
            self.create_question("待确认", status="pending"),
            self.create_question("只有旧版本已确认", version=2),
        ]
        self.assertEqual(self.client.get(f"{EXCELLENT}/list").status_code, 401)
        page = self.read_list()
        self.assertEqual(page["total"], 1)
        card = page["items"][0]
        self.assertEqual(card["id"], public)
        self.assertEqual(card["max_teacher_rating"], 4)
        self.assertIs(card["has_illustration"], True)
        for key in ("versions", "confirmations", "task_id", "comment", "answer", "illustration_url"):
            self.assertNotIn(key, card)

        response = self.client.get(f"{EXCELLENT}/{public}", headers=self.reader)
        self.assertEqual(response.status_code, 200, response.text)
        detail = response.json()
        self.assertEqual(detail["answer"], "F = ma")
        self.assertEqual(detail["illustration_url"], "/illustrations/newton.svg")
        self.assertEqual([record["version"] for record in detail["confirmations"]], [2])
        for key in ("versions", "task_id", "comment"):
            self.assertNotIn(key, detail)
        for question_id in hidden:
            with self.subTest(question_id=question_id):
                self.assertEqual(
                    self.client.get(f"{EXCELLENT}/{question_id}", headers=self.reader).status_code, 404,
                )

    def test_sort_search_and_page_summary(self):
        older = self.create_question("Straße 运动", rating=5)
        lower = self.create_question("惯性", rating=4, created_at="2026-01-03T12:00:00+00:00")
        newer = self.create_question("STRASSE 受力", rating=5, created_at="2026-01-02T12:00:00+00:00")

        first = self.read_list(sort_by="max_rating", page_size=2)
        second = self.read_list(sort_by="max_rating", page_size=2, page=2)
        self.assertEqual((first["total"], second["total"], second["page"]), (3, 3, 2))
        self.assertEqual([item["id"] for item in first["items"]], [newer, older])
        self.assertEqual([item["id"] for item in second["items"]], [lower])
        ascending = self.read_list(sort_by="max_rating", sort_order="asc")
        self.assertEqual([item["id"] for item in ascending["items"]], [lower, older, newer])
        self.assertEqual(
            [item["id"] for item in self.read_list(sort_by="created_at")["items"]],
            [lower, newer, older],
        )
        self.assertEqual(self.read_list(keyword=" strasse ")["total"], 2)
        self.assertEqual(self.read_list(keyword="apply newton")["total"], 3)
        self.assertEqual(self.read_list(keyword="%")["total"], 0)
        self.assertEqual(self.read_list(page=5, page_size=2)["items"], [])

    def test_edit_and_lowered_rating_withdraw_the_public_exercise(self):
        question_id = self.create_question("可撤下的习题")
        self.post(question_id, self.reader)
        question_url = f"{QUESTIONS}/{question_id}"
        response = self.client.patch(
            question_url,
            headers=self.owner,
            json={
                "version": 1, "title": "第二版", "content": "修订题干",
                "answer": "F = ma", "explanation": "修订解析",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

        def assert_hidden():
            self.assertEqual(self.read_list()["total"], 0)
            self.assertEqual(
                self.client.get(f"{EXCELLENT}/{question_id}", headers=self.reader).status_code, 404,
            )
            self.assertEqual(
                self.client.get(
                    f"{DISCUSSIONS}/list", headers=self.reader, params={"question_id": question_id},
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    f"{DISCUSSIONS}/post", headers=self.reader,
                    json={"question_id": question_id, "content": "无法发布到已撤下的题"},
                ).status_code,
                404,
            )

        assert_hidden()
        response = self.client.post(f"{question_url}/confirm", headers=self.owner, json={"version": 2})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.read_list()["items"][0]["version"], 2)
        self.assertEqual(self.read_discussions(question_id)["total"], 1)
        response = self.client.post(f"{question_url}/rating", headers=self.owner, json={"rating": 3})
        self.assertEqual(response.status_code, 200, response.text)
        assert_hidden()

    def test_replies_cannot_cross_exercises_and_identity_comes_from_session(self):
        _, outsider = self.create_account("outsider")
        _, admin = self.create_account("admin-test", role="ADMIN")
        question_id = self.create_question("第一题")
        other_question = self.create_question("第二题")
        root = self.post(question_id, self.reader, " 讨论正文 ", user_id=self.owner_id)
        self.assertEqual(root["user_id"], self.reader_id)
        self.assertEqual(root["username"], "reader")
        self.assertEqual(root["content"], "讨论正文")

        reply = self.post(question_id, self.owner, parent_id=root["id"])
        nested_reply = self.post(question_id, self.reader, parent_id=reply["id"])
        self.assertEqual((reply["reply_to_username"], nested_reply["reply_to_username"]), ("reader", "owner"))
        self.assertEqual(nested_reply["parent_id"], root["id"])
        page = self.read_discussions(question_id)
        self.assertEqual(page["total"], 1)
        self.assertEqual([item["id"] for item in page["items"][0]["replies"]], [reply["id"], nested_reply["id"]])
        cross_question = self.client.post(
            f"{DISCUSSIONS}/post", headers=self.reader,
            json={"question_id": other_question, "content": "串题", "parent_id": reply["id"]},
        )
        self.assertEqual(cross_question.status_code, 404)
        self.assertEqual(self.remove(root["id"], outsider, user_id=self.reader_id).status_code, 403)
        self.assertEqual(self.remove(nested_reply["id"], self.reader).status_code, 200)
        self.assertEqual(self.remove(root["id"], self.owner).status_code, 200)
        self.assertEqual(self.read_discussions(question_id)["items"], [])
        self.assertEqual(self.remove(reply["id"], admin).status_code, 404)
        another = self.post(question_id, self.reader)
        self.assertEqual(self.remove(another["id"], admin).status_code, 200)

    def test_cursor_keeps_next_discussions_after_previous_thread_is_deleted(self):
        question_id = self.create_question("讨论分页")
        ids = [self.post(question_id, self.reader, f"讨论 {index}")["id"] for index in range(5)]
        self.post(question_id, self.owner, parent_id=ids[2])
        first = self.read_discussions(question_id, page_size=2)
        self.assertEqual(first["total"], 5)
        self.assertEqual([item["id"] for item in first["items"]], ids[:2])
        self.assertEqual(first["next_after_id"], ids[1])
        self.assertEqual(self.remove(ids[1], self.owner).status_code, 200)

        next_page = self.read_discussions(question_id, page_size=2, after_id=first["next_after_id"])
        self.assertEqual(next_page["total"], 4)
        self.assertEqual([item["id"] for item in next_page["items"]], ids[2:4])
        self.assertEqual(len(next_page["items"][0]["replies"]), 1)
        self.assertEqual(next_page["next_after_id"], ids[3])
        last = self.read_discussions(question_id, page_size=2, after_id=next_page["next_after_id"])
        self.assertEqual([item["id"] for item in last["items"]], ids[4:])
        self.assertIsNone(last["next_after_id"])
        legacy_page = self.read_discussions(question_id, page_size=2, page=2)
        self.assertEqual([item["id"] for item in legacy_page["items"]], ids[3:])
