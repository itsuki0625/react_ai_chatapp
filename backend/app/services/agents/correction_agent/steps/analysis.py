import asyncio
import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from ..prompts import ANALYSIS_PROMPT
from ..tools import (
    evaluate_draft_tool,
    readability_score_tool, 
    cultural_context_check_tool,
    plagiarism_check_tool,
    fetch_policy_tool
)

logger = logging.getLogger(__name__)

class AnalysisStepAgent:
    """総合分析とスコアリングを行うステップエージェント"""
    
    def __init__(self, temperature: float = 0.3):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            max_tokens=1500
        )
        # 統合設計書のマッピングに従ったツール
        self.tools = [
            evaluate_draft_tool,        # ツール#3
            readability_score_tool,     # ツール#12
            cultural_context_check_tool, # ツール#11
            plagiarism_check_tool,      # ツール#13
            fetch_policy_tool          # ツール#6
        ]
        
    async def execute(self, statement_text: str, university_info: str = "", 
                     self_analysis_context: str = "", **kwargs) -> Dict[str, Any]:
        """
        ANALYSISステップを実行
        統合設計書に従い、5つのツールを使用して総合分析を実施
        """
        try:
            logger.info("Starting ANALYSIS step with 5 tools")
            
            # 並列実行でツールを呼び出し（パフォーマンス向上）
            tasks = [
                self._run_evaluation(statement_text, university_info),
                self._run_readability_check(statement_text),
                self._run_cultural_check(statement_text),
                self._run_plagiarism_check(statement_text),
                self._run_policy_fetch(university_info) if university_info else self._mock_policy()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            evaluation_result = results[0] if not isinstance(results[0], Exception) else {}
            readability_result = results[1] if not isinstance(results[1], Exception) else {}
            cultural_result = results[2] if not isinstance(results[2], Exception) else {}
            plagiarism_result = results[3] if not isinstance(results[3], Exception) else {}
            policy_result = results[4] if not isinstance(results[4], Exception) else {}
            
            # 総合分析の実行
            comprehensive_analysis = await self._synthesize_analysis(
                statement_text, evaluation_result, readability_result,
                cultural_result, plagiarism_result, policy_result
            )
            
            return {
                "step": "ANALYSIS",
                "status": "completed",
                "analysis": comprehensive_analysis,
                "tool_results": {
                    "evaluation": evaluation_result,
                    "readability": readability_result,
                    "cultural_check": cultural_result,
                    "plagiarism_check": plagiarism_result,
                    "university_policy": policy_result
                },
                "next_recommended_steps": self._recommend_next_steps(comprehensive_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in ANALYSIS step: {e}")
            return {
                "step": "ANALYSIS",
                "status": "error",
                "error": str(e),
                "analysis": self._fallback_analysis(statement_text)
            }
    
    async def _run_evaluation(self, statement_text: str, university_info: str) -> Dict[str, Any]:
        """ツール#3: Rubric評価実行"""
        try:
            result = await evaluate_draft_tool.ainvoke({
                "text": statement_text,
                "university_info": university_info,
                "rubric_type": "comprehensive"
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Evaluation tool error: {e}")
            return {"error": str(e)}
    
    async def _run_readability_check(self, statement_text: str) -> Dict[str, Any]:
        """ツール#12: 可読性スコア計算"""
        try:
            result = await readability_score_tool.ainvoke({"text": statement_text})
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Readability tool error: {e}")
            return {"error": str(e)}
    
    async def _run_cultural_check(self, statement_text: str) -> Dict[str, Any]:
        """ツール#11: 文化的コンテキストチェック"""
        try:
            result = await cultural_context_check_tool.ainvoke({"text": statement_text})
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Cultural check tool error: {e}")
            return {"error": str(e)}
    
    async def _run_plagiarism_check(self, statement_text: str) -> Dict[str, Any]:
        """ツール#13: 盗用チェック"""
        try:
            result = await plagiarism_check_tool.ainvoke({"text": statement_text})
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Plagiarism check tool error: {e}")
            return {"error": str(e)}
    
    async def _run_policy_fetch(self, university_info: str) -> Dict[str, Any]:
        """ツール#6: 大学ポリシー取得"""
        try:
            # university_infoから大学名を抽出（簡易実装）
            university_name = university_info.split("大学")[0] + "大学" if "大学" in university_info else university_info
            result = await fetch_policy_tool.ainvoke({
                "university_name": university_name,
                "department_name": None
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Policy fetch tool error: {e}")
            return {"error": str(e)}
    
    async def _mock_policy(self) -> Dict[str, Any]:
        """大学情報がない場合のモックポリシー"""
        return {
            "university_name": "一般的な大学",
            "admission_policy": "主体的に学習に取り組む学生を求めています",
            "key_values": ["主体性", "創造性", "社会貢献"]
        }
    
    async def _synthesize_analysis(self, statement_text: str, evaluation: Dict, 
                                 readability: Dict, cultural: Dict, 
                                 plagiarism: Dict, policy: Dict) -> Dict[str, Any]:
        """5つのツール結果を統合して総合分析を生成"""
        try:
            synthesis_prompt = f"""{ANALYSIS_PROMPT}

志望理由書:
{statement_text}

各ツールの分析結果:
1. 評価結果: {json.dumps(evaluation, ensure_ascii=False)}
2. 可読性: {json.dumps(readability, ensure_ascii=False)}
3. 文化的適切性: {json.dumps(cultural, ensure_ascii=False)}
4. 重複チェック: {json.dumps(plagiarism, ensure_ascii=False)}
5. 大学ポリシー: {json.dumps(policy, ensure_ascii=False)}

これらの結果を統合し、4つの観点（構造・内容・表現・一貫性）から総合分析を行ってください。
"""
            
            response = await self.llm.ainvoke(synthesis_prompt)
            
            # 統合分析結果の構造化
            synthesis_result = {
                "overall_score": evaluation.get("overall_score", 75),
                "dimension_scores": {
                    "structure": evaluation.get("structure_score", 75),
                    "content": evaluation.get("content_score", 75),
                    "expression": evaluation.get("expression_score", 80),
                    "coherence": evaluation.get("coherence_score", 70)
                },
                "readability_assessment": {
                    "score": readability.get("readability_score", 70),
                    "level": readability.get("level", "普通")
                },
                "cultural_appropriateness": {
                    "score": cultural.get("appropriateness_score", 9.0),
                    "issues": cultural.get("cultural_issues", [])
                },
                "originality_assessment": {
                    "similarity_rate": plagiarism.get("similarity_percentage", 0),
                    "risk_level": plagiarism.get("risk_level", "低い")
                },
                "university_alignment": {
                    "policy_match": self._calculate_policy_match(statement_text, policy),
                    "alignment_suggestions": ["より具体的な大学との関連性を記述"]
                },
                "comprehensive_feedback": response.content,
                "priority_improvements": self._identify_priority_improvements(evaluation, readability, cultural, plagiarism)
            }
            
            return synthesis_result
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return self._fallback_analysis(statement_text)
    
    def _calculate_policy_match(self, statement_text: str, policy: Dict) -> float:
        """大学ポリシーとの適合度を簡易計算"""
        if not policy or "key_values" not in policy:
            return 7.0
        
        key_values = policy.get("key_values", [])
        match_count = 0
        
        for value in key_values:
            if value in statement_text:
                match_count += 1
        
        return min(10.0, 5.0 + (match_count / len(key_values)) * 5.0) if key_values else 7.0
    
    def _identify_priority_improvements(self, evaluation: Dict, readability: Dict, 
                                      cultural: Dict, plagiarism: Dict) -> list:
        """優先改善項目を特定"""
        improvements = []
        
        # 評価スコアが低い項目
        scores = evaluation.get("dimension_scores", {}) or {
            "structure": evaluation.get("structure_score", 75),
            "content": evaluation.get("content_score", 75),
            "expression": evaluation.get("expression_score", 80),
            "coherence": evaluation.get("coherence_score", 70)
        }
        
        for dimension, score in scores.items():
            if score < 75:
                improvements.append(f"{dimension}の改善（現在スコア: {score}）")
        
        # 可読性が低い場合
        if readability.get("readability_score", 70) < 70:
            improvements.append("文章の可読性向上")
        
        # 文化的問題がある場合
        if cultural.get("cultural_issues", []):
            improvements.append("表現の適切性確認")
        
        # 重複率が高い場合
        if plagiarism.get("similarity_percentage", 0) > 20:
            improvements.append("オリジナリティの向上")
        
        return improvements[:3]  # 上位3項目
    
    def _recommend_next_steps(self, analysis: Dict) -> list:
        """次のステップを推奨"""
        recommendations = []
        
        overall_score = analysis.get("overall_score", 75)
        
        if overall_score < 70:
            recommendations.extend(["STRUCTURE", "CONTENT"])
        elif overall_score < 80:
            recommendations.extend(["CONTENT", "EXPRESSION"])
        else:
            recommendations.extend(["EXPRESSION", "POLISH"])
        
        return recommendations
    
    def _fallback_analysis(self, statement_text: str) -> Dict[str, Any]:
        """エラー時のフォールバック分析"""
        word_count = len(statement_text.replace(' ', '').replace('\n', ''))
        
        return {
            "overall_score": 70,
            "dimension_scores": {
                "structure": 70,
                "content": 70,
                "expression": 75,
                "coherence": 70
            },
            "comprehensive_feedback": "基本的な分析を実行しました。より詳細な分析のため、再実行をお試しください。",
            "word_count": word_count,
            "priority_improvements": ["詳細分析の再実行をお勧めします"]
        } 