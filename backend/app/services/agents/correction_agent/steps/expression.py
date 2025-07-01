import asyncio
import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from ..prompts import EXPRESSION_PROMPT
from ..tools import (
    tone_style_adjust_tool,
    grammar_check_tool,
    cultural_context_check_tool
)

logger = logging.getLogger(__name__)

class ExpressionStepAgent:
    """表現・語調調整を行うステップエージェント"""
    
    def __init__(self, temperature: float = 0.4):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            max_tokens=1200
        )
        # 統合設計書のマッピングに従ったツール
        self.tools = [
            tone_style_adjust_tool,        # ツール#2
            grammar_check_tool,           # ツール#10
            cultural_context_check_tool   # ツール#11
        ]
    
    async def execute(self, statement_text: str, university_info: str = "",
                     self_analysis_context: str = "", target_tone: str = "formal",
                     target_style: str = "confident", **kwargs) -> Dict[str, Any]:
        """
        EXPRESSIONステップを実行
        統合設計書に従い、3つのツールを使用して表現改善を実施
        """
        try:
            logger.info("Starting EXPRESSION step with 3 tools")
            
            # 3つのツールを並列実行
            tasks = [
                self._run_tone_style_adjustment(statement_text, target_tone, target_style),
                self._run_grammar_check(statement_text),
                self._run_cultural_check(statement_text)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            tone_result = results[0] if not isinstance(results[0], Exception) else {}
            grammar_result = results[1] if not isinstance(results[1], Exception) else {}
            cultural_result = results[2] if not isinstance(results[2], Exception) else {}
            
            # 表現改善の総合評価
            expression_improvements = await self._synthesize_expression_improvements(
                statement_text, tone_result, grammar_result, cultural_result, 
                target_tone, target_style
            )
            
            return {
                "step": "EXPRESSION",
                "status": "completed",
                "expression": {
                    "tone_style_analysis": tone_result,
                    "grammar_analysis": grammar_result,
                    "cultural_analysis": cultural_result,
                    "integrated_improvements": expression_improvements,
                    "quality_scores": self._calculate_quality_scores(tone_result, grammar_result, cultural_result)
                },
                "recommended_changes": self._extract_expression_recommendations(expression_improvements),
                "next_recommended_steps": ["COHERENCE", "POLISH"]
            }
            
        except Exception as e:
            logger.error(f"Error in EXPRESSION step: {e}")
            return {
                "step": "EXPRESSION",
                "status": "error",
                "error": str(e),
                "expression": self._fallback_expression_analysis(statement_text)
            }
    
    async def _run_tone_style_adjustment(self, statement_text: str, target_tone: str, target_style: str) -> Dict[str, Any]:
        """ツール#2: 語調・スタイル調整"""
        try:
            result = await tone_style_adjust_tool.ainvoke({
                "text": statement_text,
                "target_tone": target_tone,
                "target_style": target_style
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Tone style adjustment error: {e}")
            return {"error": str(e)}
    
    async def _run_grammar_check(self, statement_text: str) -> Dict[str, Any]:
        """ツール#10: 文法チェック"""
        try:
            result = await grammar_check_tool.ainvoke({"text": statement_text})
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Grammar check error: {e}")
            return {"error": str(e)}
    
    async def _run_cultural_check(self, statement_text: str) -> Dict[str, Any]:
        """ツール#11: 文化的コンテキストチェック"""
        try:
            result = await cultural_context_check_tool.ainvoke({"text": statement_text})
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Cultural context check error: {e}")
            return {"error": str(e)}
    
    async def _synthesize_expression_improvements(self, statement_text: str, tone_result: Dict,
                                                grammar_result: Dict, cultural_result: Dict,
                                                target_tone: str, target_style: str) -> Dict[str, Any]:
        """3つのツール結果を統合して表現改善案を生成"""
        try:
            synthesis_prompt = f"""{EXPRESSION_PROMPT}

現在の志望理由書:
{statement_text}

語調・スタイル分析結果:
{json.dumps(tone_result, ensure_ascii=False, indent=2)}

文法チェック結果:
{json.dumps(grammar_result, ensure_ascii=False, indent=2)}

文化的コンテキスト分析結果:
{json.dumps(cultural_result, ensure_ascii=False, indent=2)}

目標語調: {target_tone}
目標スタイル: {target_style}

これらの分析結果を統合し、以下の観点から表現改善案を提示してください：
1. 語調・文体の一貫性
2. 文法・語法の正確性
3. 文化的適切性
4. 読み手への印象
5. 全体的な表現力

具体的な修正案と改善理由を提示してください。
"""
            
            response = await self.llm.ainvoke(synthesis_prompt)
            
            # 統合改善案の構造化
            improvements = {
                "comprehensive_assessment": response.content,
                "priority_fixes": self._identify_priority_fixes(tone_result, grammar_result, cultural_result),
                "tone_consistency": self._assess_tone_consistency(tone_result, target_tone, target_style),
                "grammar_corrections": self._extract_grammar_corrections(grammar_result),
                "cultural_adjustments": self._extract_cultural_adjustments(cultural_result),
                "style_enhancements": self._suggest_style_enhancements(tone_result, target_style),
                "overall_expression_score": self._calculate_overall_expression_score(tone_result, grammar_result, cultural_result)
            }
            
            return improvements
            
        except Exception as e:
            logger.error(f"Expression synthesis error: {e}")
            return {"error": str(e)}
    
    def _identify_priority_fixes(self, tone_result: Dict, grammar_result: Dict, cultural_result: Dict) -> list:
        """優先修正項目を特定"""
        priority_fixes = []
        
        # 文法エラーの優先度チェック
        grammar_issues = grammar_result.get("issues", [])
        high_priority_grammar = [issue for issue in grammar_issues if issue.get("type") in ["grammar", "syntax"]]
        if high_priority_grammar:
            priority_fixes.extend([{
                "type": "grammar",
                "description": issue.get("message", ""),
                "priority": "high",
                "suggestion": issue.get("suggestion", "")
            } for issue in high_priority_grammar[:3]])  # 上位3件
        
        # 文化的問題の優先度チェック
        cultural_issues = cultural_result.get("cultural_issues", [])
        if cultural_issues:
            priority_fixes.extend([{
                "type": "cultural",
                "description": issue.get("issue", ""),
                "priority": "medium",
                "suggestion": issue.get("suggestion", "")
            } for issue in cultural_issues[:2]])  # 上位2件
        
        # 語調の不一致チェック
        tone_score = tone_result.get("tone_score", 8.0)
        style_score = tone_result.get("style_score", 8.0)
        if tone_score < 7.0 or style_score < 7.0:
            priority_fixes.append({
                "type": "tone_style",
                "description": "語調・スタイルの調整が必要",
                "priority": "medium",
                "suggestion": "一貫した語調とスタイルに統一"
            })
        
        return priority_fixes
    
    def _assess_tone_consistency(self, tone_result: Dict, target_tone: str, target_style: str) -> Dict[str, Any]:
        """語調の一貫性を評価"""
        tone_score = tone_result.get("tone_score", 0)
        style_score = tone_result.get("style_score", 0)
        
        return {
            "current_tone_score": tone_score,
            "current_style_score": style_score,
            "target_tone": target_tone,
            "target_style": target_style,
            "consistency_level": "high" if tone_score >= 8.0 and style_score >= 8.0 else "medium" if tone_score >= 6.0 and style_score >= 6.0 else "low",
            "improvement_needed": tone_score < 7.0 or style_score < 7.0,
            "specific_adjustments": self._generate_tone_adjustments(tone_result, target_tone, target_style)
        }
    
    def _extract_grammar_corrections(self, grammar_result: Dict) -> list:
        """文法修正案を抽出"""
        corrections = []
        
        issues = grammar_result.get("issues", [])
        for issue in issues:
            corrections.append({
                "issue_type": issue.get("type", "unknown"),
                "message": issue.get("message", ""),
                "suggestion": issue.get("suggestion", ""),
                "confidence": "high" if issue.get("type") in ["grammar", "punctuation"] else "medium"
            })
        
        return corrections[:5]  # 上位5件
    
    def _extract_cultural_adjustments(self, cultural_result: Dict) -> list:
        """文化的調整案を抽出"""
        adjustments = []
        
        cultural_issues = cultural_result.get("cultural_issues", [])
        for issue in cultural_issues:
            adjustments.append({
                "issue": issue.get("issue", ""),
                "reason": issue.get("reason", ""),
                "adjustment": issue.get("suggestion", ""),
                "importance": "high"
            })
        
        return adjustments
    
    def _suggest_style_enhancements(self, tone_result: Dict, target_style: str) -> list:
        """スタイル向上提案を生成"""
        enhancements = []
        
        # 目標スタイルに基づく提案
        style_suggestions = {
            "confident": [
                "断定的な表現を増やす",
                "具体的な成果や数値を強調",
                "積極的な意志表現を使用"
            ],
            "humble": [
                "謙虚な表現を適切に使用",
                "学習姿勢を前面に出す",
                "感謝の気持ちを表現"
            ],
            "passionate": [
                "情熱的な語彙を適切に使用",
                "動機の強さを表現",
                "未来への意欲を強調"
            ]
        }
        
        enhancements.extend(style_suggestions.get(target_style, []))
        
        # 現在のスタイルスコアに基づく追加提案
        current_style_score = tone_result.get("style_score", 0)
        if current_style_score < 7.0:
            enhancements.append("文章全体の表現力を向上")
        
        return enhancements
    
    def _generate_tone_adjustments(self, tone_result: Dict, target_tone: str, target_style: str) -> list:
        """具体的な語調調整案を生成"""
        adjustments = []
        
        changes = tone_result.get("changes", [])
        for change in changes:
            adjustments.append({
                "original": change.get("original", ""),
                "adjusted": change.get("adjusted", ""), 
                "reason": change.get("reason", f"{target_tone}・{target_style}への調整")
            })
        
        return adjustments[:3]  # 上位3件
    
    def _calculate_quality_scores(self, tone_result: Dict, grammar_result: Dict, cultural_result: Dict) -> Dict[str, float]:
        """品質スコアを計算"""
        return {
            "tone_score": tone_result.get("tone_score", 7.0),
            "style_score": tone_result.get("style_score", 7.0),
            "grammar_score": grammar_result.get("grammar_score", 85) / 10,  # 100点満点を10点満点に変換
            "cultural_appropriateness": cultural_result.get("appropriateness_score", 8.5),
            "overall_expression": (
                tone_result.get("tone_score", 7.0) +
                tone_result.get("style_score", 7.0) +
                (grammar_result.get("grammar_score", 85) / 10) +
                cultural_result.get("appropriateness_score", 8.5)
            ) / 4
        }
    
    def _calculate_overall_expression_score(self, tone_result: Dict, grammar_result: Dict, cultural_result: Dict) -> float:
        """総合表現スコアを計算"""
        quality_scores = self._calculate_quality_scores(tone_result, grammar_result, cultural_result)
        return round(quality_scores["overall_expression"], 1)
    
    def _extract_expression_recommendations(self, expression_improvements: Dict) -> list:
        """表現改善の推奨事項を抽出"""
        recommendations = []
        
        # 優先修正項目から推奨事項を抽出
        priority_fixes = expression_improvements.get("priority_fixes", [])
        for fix in priority_fixes:
            if fix.get("priority") == "high":
                recommendations.append({
                    "type": fix.get("type", ""),
                    "description": fix.get("description", ""),
                    "action": fix.get("suggestion", ""),
                    "priority": fix.get("priority", "medium")
                })
        
        # 語調の一貫性から推奨事項を抽出
        tone_consistency = expression_improvements.get("tone_consistency", {})
        if tone_consistency.get("improvement_needed", False):
            recommendations.append({
                "type": "tone_consistency",
                "description": "語調の一貫性を向上",
                "action": "統一された語調とスタイルに調整",
                "priority": "medium"
            })
        
        return recommendations[:5]  # 上位5件
    
    def _fallback_expression_analysis(self, statement_text: str) -> Dict[str, Any]:
        """エラー時のフォールバック分析"""
        return {
            "basic_assessment": {
                "word_count": len(statement_text.replace(' ', '').replace('\n', '')),
                "estimated_tone": "formal",
                "estimated_style": "neutral",
                "basic_issues": ["詳細な分析が必要"]
            },
            "general_suggestions": [
                "語調の一貫性を確認",
                "文法・語法をチェック",
                "表現の適切性を見直し"
            ],
            "quality_scores": {
                "tone_score": 7.0,
                "style_score": 7.0,
                "grammar_score": 7.5,
                "cultural_appropriateness": 8.0,
                "overall_expression": 7.4
            },
            "error_note": "技術的問題により詳細な表現分析が実行できませんでした"
        } 