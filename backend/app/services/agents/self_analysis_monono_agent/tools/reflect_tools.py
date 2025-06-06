from typing import List

def rank_insights(insights: List[str]) -> List[str]:
    """TF-IDF と novelty score を組み合わせて上位 5 行の洞察リストを返します。"""
    # TODO: 実装 (TF-IDF と novelty の計算)
    # 現状は単純に先頭 5 件を返却
    return insights[:5] 