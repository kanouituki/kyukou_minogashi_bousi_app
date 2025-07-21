from openai import OpenAI
import json
from config import Config, get_logger

logger = get_logger(__name__)

# OpenAI クライアントを初期化
client = OpenAI(api_key=Config.OPENAI_API_KEY)

def analyze_announcement(title: str, body: str) -> dict:
    """
    OpenAI APIを使用して、お知らせが休講情報であるかを判定し、構造化された情報を返します。
    """
    prompt = f"""以下の授業のお知らせが休講情報であるか判定し、もし休講情報であれば以下のJSON形式で情報を抽出してください。
休講でなければ、canceledをfalseとしてください。

情報が不足している場合は、該当フィールドをnullとしてください。
日付はYYYY-MM-DD形式で、時限は「1限」「2限」のように記述してください。

お知らせのタイトル: {title}
お知らせの本文: {body}

出力JSON形式:
```json
{{
  "course": "授業名",
  "date": "YYYY-MM-DD",
  "period": "時限",
  "canceled": true/false,
  "source": "KLMS",
  "message": "休講に関する短いメッセージ"
}}
```

JSONのみを出力してください。追加のテキストや説明は含めないでください。
"""

    try:
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=Config.OPENAI_TEMPERATURE,
            max_tokens=Config.OPENAI_MAX_TOKENS
        )
        
        # 応答からJSON文字列を抽出し、パースする
        analysis_result_str = response.choices[0].message.content
        
        # マークダウンのコードブロックを除去
        if analysis_result_str.startswith("```json"):
            analysis_result_str = analysis_result_str[7:]  # ```json を除去
        if analysis_result_str.startswith("```"):
            analysis_result_str = analysis_result_str[3:]  # ``` を除去
        if analysis_result_str.endswith("```"):
            analysis_result_str = analysis_result_str[:-3]  # ``` を除去
        
        analysis_result_str = analysis_result_str.strip()
        analysis_result = json.loads(analysis_result_str)
        return analysis_result
    except Exception as e:
        logger.error(f"OpenAI APIエラーまたはJSON解析エラーが発生しました: {e}")
        # より詳細なエラー情報を表示するために、元のエラーメッセージと生レスポンスを含める
        return {"error": str(e), "raw_response": response.choices[0].message.content if 'response' in locals() and response.choices else 'N/A'}

if __name__ == "__main__":
    logger.info("OpenAI GPTによる休講判定テストを開始します...")

    # テスト用のお知らせデータ（休講の例）
    test_title_cancellation = "【重要】〇〇ゼミ 6/17(火) 3限 休講のお知らせ"
    test_body_cancellation = "教員の急病のため、6月17日（火）3限の〇〇ゼミは休講といたします。補講については別途お知らせします。"
    
    # テスト用のお知らせデータ（通常のお知らせの例）
    test_title_normal = "〇〇ゼミ 次回授業のお知らせ"
    test_body_normal = "次回の授業は6月24日（火）3限に通常通り実施します。課題の提出を忘れないようにしてください。"

    logger.info("休講判定テスト (休講の例):")
    result_cancellation = analyze_announcement(test_title_cancellation, test_body_cancellation)
    logger.info(json.dumps(result_cancellation, indent=2, ensure_ascii=False))

    logger.info("休講判定テスト (通常のお知らせの例):")
    result_normal = analyze_announcement(test_title_normal, test_body_normal)
    logger.info(json.dumps(result_normal, indent=2, ensure_ascii=False))

    logger.info("OpenAI GPTによる休講判定テストを終了します。") 