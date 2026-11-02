"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    if lecture < 1:
        return "講義回は1以上の整数で指定してください。"

    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、講義回を指定した復習用の
    問題を求められたときに使う。
    """
    if lecture < 1:
        return "講義回は1以上の整数で指定してください。"

    terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語が用語集にありません。別の回を指定してください。"

    term = random.choice(terms)
    return json.dumps(
        {
            "question": f"「{term['term']}」の意味は？",
            "answer": term["definition"],
        },
        ensure_ascii=False,
    )


def ice_break(character: str, topic: str | None = None) -> str:
    """キャラクター設定と人間以外の生物を題材に、会話冒頭の挨拶を作る材料を返す。

    題材を省略すると、動物など人間以外の生物から選ぶ。
    例: character="関西弁の宇宙飛行士", topic="ペンギン"。
    会話の始まりや回答に短いアイスブレイクを添えるときに使う。
    """
    character = character.strip()
    if not character:
        return "アイスブレイクを作るため、キャラクター設定を指定してください。"
    topic = (topic or "").strip() or random.choice(
        ("猫", "ペンギン", "イルカ", "ミツバチ", "カメ")
    )

    return (
        "次のキャラクター設定と題材を使い、会話の冒頭に自然に添えられる、"
        "短く親しみやすい挨拶を1〜2文で作ってください。\n"
        f"キャラクター設定: {character}\n"
        f"題材: {topic}"
    )
