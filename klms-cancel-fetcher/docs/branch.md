本プロジェクトでは、**誰が見ても分かりやすいブランチ名とコミットメッセージ**を使い、チーム内の混乱を防ぎます。

---

## ✅ ブランチ命名ルール

### 基本構文

```
<ステータス>/<カテゴリ>/<概要（英数字 or 簡潔な英単語）>
```

例：

```yaml
wip/feature/discord-command
done/fix/scraping-error
review/refactor/env-loader
```

---

### ステータス一覧（日本語訳つき）

| ステータス | 意味                           |
|------------|--------------------------------|
| `wip`      | 作業中（Work In Progress）     |
| `review`   | レビュー待ち                    |
| `done`     | 完了（マージ・リリース済み）   |
| `hotfix`   | 緊急修正                        |

> ✅ **作業が完了してPRを出すときは `review/〜` にリネームしてもOKです**

---

### カテゴリ一覧（英語＋日本語）

| カテゴリ    | 用途                                |
|-------------|-------------------------------------|
| `feature`   | 新しい機能                          |
| `fix`       | バグ修正                            |
| `refactor`  | 中のコード整理（動きは同じ）        |
| `docs`      | ドキュメント変更（READMEなど）      |
| `chore`     | 設定・依存・CI変更など                |

---

### ブランチ名の例

| 用途               | ブランチ名例                          |
|--------------------|---------------------------------------|
| Discord機能作成     | `wip/feature/discord-command`         |
| スクレイピング修正   | `wip/fix/scraping-error`             |
| SQLite周りの整理    | `wip/refactor/sqlite-handler`        |
| README追加         | `wip/docs/add-usage-guide`           |
| secretsの設定変更 | `wip/chore/update-secrets`           |

---

## 📝 コミットメッセージ命名ルール

### 構文

```markdown
<タイプ>: <変更内容の簡潔な説明（日本語）>
```

### タイプ一覧

| タイプ      | 意味                                | 例                               |
|-------------|-------------------------------------|----------------------------------|
| `feat`      | 新しい機能                          | `feat: Discordコマンドを追加`    |
| `fix`       | バグ修正                            | `fix: スクレイピングの403対応`   |
| `refactor`  | リファクタ（動作変更なし）           | `refactor: 認証処理を関数に整理` |
| `docs`      | ドキュメント                        | `docs: READMEに使用方法を追記`  |
| `chore`     | 設定、CI、ビルド                     | `chore: GitHub Actionsを追加`   |
| `test`      | テストコードの追加・修正              | `test: 通知部分のテスト追加`     |

> 💡 **説明は必ず日本語で、動作や目的が一目でわかるようにしましょう**

---

### コミット例

```yaml
feat: Discordで空き状況を表示する機能を追加
fix: Playwrightがタイムアウトするバグ修正
refactor: 通知処理を notifier.py に移動
docs: 使用手順のセクションをREADMEに追加
chore: .env.example を追加
```

---

## 📌 その他の運用ルール

- ✅ 動作確認済みのブランチは `done/〜` にリネームしておくとわかりやすいです
- 🚫 `main` ブランチに直接pushしない（PR経由でマージする）
- ✅ 作業中は `wip/〜`、レビュー依頼時に `review/〜` に変えてもOK

---

## 🔁 よくある運用例

1. 作業開始：
```markdown
git checkout -b wip/feature/discord-bot
```

2. 実装 → commit：
```markdown
git commit -m "feat: Discordコマンドを追加"
```

3. 完了 → レビュー依頼：
```markdown
git branch -m review/feature/discord-bot
```

4. レビュー後、マージ：
```markdown
git checkout main
git merge review/feature/discord-bot
```

5. ブランチ削除 or `done/〜` にリネーム：
```yaml
git branch -d review/feature/discord-bot
```

---

このルールを守れば、英語が苦手でも作業中・レビュー中・完了ブランチがひと目で分かり、安心して共同開発できます。 