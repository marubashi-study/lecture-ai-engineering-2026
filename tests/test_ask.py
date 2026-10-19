"""質問スクリプトのテスト（LLMもAPIキーも使わない）。"""

import sys
from types import SimpleNamespace
from unittest.mock import Mock

from app import ask as ask_module


def test_interactive_reuses_chat_for_conversation(monkeypatch, capsys):
    client = Mock()
    chat = Mock()
    client.chats.create.return_value = chat
    chat.send_message.side_effect = [
        SimpleNamespace(text="最初の回答", usage_metadata=None),
        SimpleNamespace(text="続きの回答", usage_metadata=None),
    ]
    monkeypatch.setattr(ask_module.genai, "Client", Mock(return_value=client))
    monkeypatch.setattr(ask_module, "get_api_key", Mock(return_value="test-key"))
    questions = iter(["最初の質問", "続きの質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.interactive(model="test-model")

    ask_module.genai.Client.assert_called_once_with(api_key="test-key")
    client.chats.create.assert_called_once()
    assert client.chats.create.call_args.kwargs["model"] == "test-model"
    assert [call.args[0] for call in chat.send_message.call_args_list] == [
        "最初の質問",
        "続きの質問",
    ]
    output = capsys.readouterr().out
    assert "最初の回答" in output
    assert "続きの回答" in output


def test_ask_prints_latency_and_token_counts(monkeypatch, capsys):
    client = Mock()
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=5),
    )
    client.chats.create.return_value.send_message.return_value = response
    client_constructor = Mock(return_value=client)
    monkeypatch.setattr(ask_module.genai, "Client", client_constructor)
    monkeypatch.setattr(ask_module, "get_api_key", Mock(return_value="test-key"))
    timestamps = iter([10.0, 11.234])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(timestamps))

    assert ask_module.ask("質問", model="test-model") == "回答"

    assert client.chats.create.call_args.kwargs["model"] == "test-model"
    assert capsys.readouterr().out == (
        "[計測] 応答時間: 1.23秒, 入力トークン: 12, 出力トークン: 5\n"
    )


def test_main_passes_model_option_to_ask(monkeypatch, capsys):
    ask = Mock(return_value="回答")
    monkeypatch.setattr(ask_module, "ask", ask)
    monkeypatch.setattr(
        sys,
        "argv",
        ["app.ask", "--model", "test-model", "質問"],
    )

    ask_module.main()

    ask.assert_called_once_with("質問", model="test-model")
    assert "[model] test-model" in capsys.readouterr().out