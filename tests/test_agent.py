"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary", "make_quiz", "ice_break"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # 承認が必要なツール（requires_approval=True）は、実行されずに承認待ちになるので戻り値が無い
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_all_tools_handle_test_model_dummy_arguments_without_api_key():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("テスト")

    calls = {part.tool_name: part.args for part in _parts(result, ToolCallPart)}
    returns = {part.tool_name: str(part.content) for part in _parts(result, ToolReturnPart)}

    assert set(calls) == BASE_TOOLS
    assert calls["get_lecture_summary"] == {"lecture": 0}
    assert calls["make_quiz"] == {"lecture": 0}
    assert set(returns) == BASE_TOOLS
    assert "1以上の整数" in returns["get_lecture_summary"]
    assert "1以上の整数" in returns["make_quiz"]
    assert "キャラクター設定" in returns["ice_break"]
    assert "題材" in returns["ice_break"]


def test_quiz_instructions_put_animal_ice_break_before_the_quiz():
    from app.agent import INSTRUCTIONS

    assert "ice_break を先に呼び" in INSTRUCTIONS
    assert "回答の先頭に置いてから、問題を続ける" in INSTRUCTIONS
    assert "人間以外の生物" in INSTRUCTIONS
