from typing import List

# 有効な感情ラベルのマスターセット
MASTER_EMOTIONS = {"喜び", "悔しさ", "焦り", "達成感", "怒り", "驚き", "悲しみ"}

async def validate_emotion(label: str) -> str:
    """
    感情ラベルがマスターセットに存在しない場合は "その他" を返します。
    """
    return label if label in MASTER_EMOTIONS else "その他"

def shorten_insight(text: str, maxlen: int = 40) -> str:
    """
    insightテキストを maxlen 文字まで切り詰めます。
    """
    return text[:maxlen] if len(text) > maxlen else text 