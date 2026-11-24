# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：
    - glossary_search_glossary
- STEP 2 の [tool call]：
    - glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：
    - fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
    - glossary_search_glossary({'query': 'MCP'})
- STEP 4 の [tool call]：
    - aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 Versioning overview'})
    - 
- 気づき・疑問：
    - MCPを用いることで、組織として定式化・統制されたツール利用の仕組みを作れる点に大きなメリットを感じました。
    一方で、bashの利用や個人で自由にMCPを作成できる環境下では、結果として制限なく多様な操作が可能になってしまうため、実運用においてはガバナンスや権限管理の設計が重要かつ難しい問題だと感じました。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：実装
- やったこと：
    - make_quizの追加とlec範囲の設定
- 結果：
    - クイズを呼び出せるようになった
    - 範囲外の回を指定した場合、1-13回となるように再度リクエストしていた
- 気づき・疑問：
    - 範囲外の値を入力した際、returnしたメッセージをAIが読み取り、自動的に入力を調整する動きは非常に興味深かった。
    - 他方、信頼できないMCPを利用した場合、これらの特性を悪用し、情報を抜き出すことが容易なように感じた。
