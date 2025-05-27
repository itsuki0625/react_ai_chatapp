from typing import List, Dict


def ngram_similarity(s: str, corpus: List[str]) -> float:
    """3-gramベースで文字列同士の類似度を計算し、最小スコアを返す"""
    sgrams = set([s[i:i+3] for i in range(len(s)-2)])
    scores: List[float] = []
    for c in corpus:
        cgrams = set([c[i:i+3] for i in range(len(c)-2)])
        union = sgrams | cgrams
        if not union:
            continue
        scores.append(len(sgrams & cgrams) / len(union))
    return min(scores) if scores else 0.0


def tone_score(vision: str) -> Dict[str, int]:
    """簡易ルールで excitement/social/feasible を 1–7 のスコアで返す"""
    # 仮実装: 文字数に応じて中間値を返す
    length = len(vision)
    base = max(1, min(7, length // 5))
    return {"excitement": base, "social": base, "feasible": base} 