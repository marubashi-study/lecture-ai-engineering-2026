"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --interactive  # 会話履歴を保って質問する
    uv run python -m app.ask --model gemini-3.5-flash "LoRAとは何ですか？"

単発モードでは、ツールも会話履歴も持たずに1回だけ質問する。
対話モードでは、同じチャットの会話履歴を保ったまま質問を続ける。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def create_chat(client, model: str):
    return client.chats.create(
        model=model,
        config=types.GenerateContentConfig(temperature=0.0),
    )
        # config=types.GenerateContentConfig(temperature=0.0, seed=42),


def _print_metrics(response, elapsed: float) -> None:
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage is not None else None
    output_tokens = usage.candidates_token_count if usage is not None else None
    input_display = input_tokens if input_tokens is not None else "不明"
    output_display = output_tokens if output_tokens is not None else "不明"
    print(
        f"[計測] 応答時間: {elapsed:.2f}秒, "
        f"入力トークン: {input_display}, 出力トークン: {output_display}"
    )


def _send_message(chat, question: str) -> str:
    started_at = time.perf_counter()
    response = chat.send_message(question)
    elapsed = time.perf_counter() - started_at
    _print_metrics(response, elapsed)
    return response.text


def ask(question: str, model: str = MODEL) -> str:
    client = genai.Client(api_key=get_api_key())
    return _send_message(create_chat(client, model), question)


def interactive(model: str = MODEL) -> None:
    client = genai.Client(api_key=get_api_key())
    chat = create_chat(client, model)
    print(f"[model] {model}")
    print("会話を終了するには exit または quit を入力してください。")
    while True:
        try:
            question = input("\n質問> ").strip()
        except EOFError:
            print()
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        print(_send_message(chat, question))


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--interactive", action="store_true", help="会話履歴を保って質問する")
    parser.add_argument("--model", default=MODEL, help=f"使用するモデル（既定: {MODEL}）")
    args = parser.parse_args()

    try:
        if args.interactive:
            interactive(model=args.model)
        else:
            print(f"[model] {args.model}")
            print(f"[質問] {args.question}\n")
            print(ask(args.question, model=args.model))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
