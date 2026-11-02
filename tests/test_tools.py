"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_lecture_tools_reject_zero_and_negative_lectures():
    for lecture in (0, -1):
        assert "1以上の整数" in tools.get_lecture_summary(lecture)
        assert "1以上の整数" in tools.make_quiz(lecture)


def test_make_quiz_uses_a_term_from_the_requested_lecture(monkeypatch):
    terms = [term for term in tools.load_glossary() if term["lecture"] == 2]
    selected = next(term for term in terms if term["term"] == "PEFT")

    def choose_term(candidates):
        assert candidates == terms
        return selected

    monkeypatch.setattr(tools.random, "choice", choose_term)

    quiz = json.loads(tools.make_quiz(2))

    assert quiz == {
        "question": f"「{selected['term']}」の意味は？",
        "answer": selected["definition"],
    }


def test_make_quiz_reports_when_lecture_has_no_terms():
    assert "第99回の用語が用語集にありません" in tools.make_quiz(99)


def test_ice_break_uses_character_and_topic():
    result = tools.ice_break("関西弁の宇宙飛行士", "最近の天気")

    assert "関西弁の宇宙飛行士" in result
    assert "最近の天気" in result
    assert "1〜2文" in result


def test_ice_break_defaults_to_a_nonhuman_living_topic(monkeypatch):
    def choose_topic(topics):
        assert topics == ("猫", "ペンギン", "イルカ", "ミツバチ", "カメ")
        return "ペンギン"

    monkeypatch.setattr(tools.random, "choice", choose_topic)
    result = tools.ice_break("関西弁の宇宙飛行士")

    assert "題材: ペンギン" in result


def test_ice_break_blank_topic_defaults_to_a_nonhuman_living_thing(monkeypatch):
    monkeypatch.setattr(tools.random, "choice", lambda topics: "ミツバチ")
    assert "題材: ミツバチ" in tools.ice_break("関西弁の宇宙飛行士", "  ")
    assert "キャラクター設定" in tools.ice_break("")


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
