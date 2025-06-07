import os
import math

from openai import AsyncOpenAI

# 抽象度が低すぎる or 意味が薄い語
NG_WORDS = {"好き", "頑張り", "IT"}
# 埋め込み類似度の閾値
THRESHOLD = 0.9

# AsyncOpenAIクライアントを初期化
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def normalize_values(session_id: str, values: list[str]) -> list[str]:
    """
    OpenAI Embeddingsで類似度を計算し、重複表記をまとめた上でNG_WORDSを除外して返します。
    """
    if not values:
        return []
    # 埋め込みを取得
    response = await client.embeddings.create(
        model="text-embedding-ada-002",
        input=values
    )
    # 各入力に対応するベクトルリスト
    embs = [item.embedding for item in response.data]
    unique = []
    unique_embs = []
    for v, emb in zip(values, embs):
        # 既存uniqueと比較
        is_dup = False
        for uemb in unique_embs:
            # コサイン類似度を計算
            dot = sum(x * y for x, y in zip(emb, uemb))
            norm1 = math.sqrt(sum(x * x for x in emb))
            norm2 = math.sqrt(sum(y * y for y in uemb))
            if norm1 > 0 and norm2 > 0 and dot / (norm1 * norm2) >= THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            unique.append(v)
            unique_embs.append(emb)
    # NGワード除外
    filtered = [v for v in unique if v not in NG_WORDS]
    return filtered 