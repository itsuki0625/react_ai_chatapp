import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from ..prompts import POLISH_PROMPT
from ..tools import (
    apply_reflexion_tool,
    diff_versions_tool,
    save_revision_tool,
    list_revisions_tool
)

logger = logging.getLogger(__name__)

class PolishStepAgent:
    """最終仕上げとリフレクションを行うステップエージェント"""
    
    def __init__(self, temperature: float = 0.3):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            max_tokens=1200
        )
        # 統合設計書のマッピングに従ったツール
        self.tools = [
            apply_reflexion_tool,  # ツール#20
            diff_versions_tool,    # ツール#15
            save_revision_tool,    # ツール#16
            list_revisions_tool    # ツール#17
        ]
    
    async def execute(self, statement_text: str, university_info: str = "",
                     self_analysis_context: str = "", statement_id: str = "",
                     original_text: str = None, evaluation_logs: List[Dict] = None,
                     improvement_history: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        POLISHステップを実行
        統合設計書に従い、4つのツールを使用して最終仕上げを実施
        """
        try:
            logger.info("Starting POLISH step with 4 tools")
            
            # 1. 過去のリビジョン履歴を取得
            revision_history = await self._get_revision_history(statement_id) if statement_id else {}
            
            # 2. リフレクション分析を実行
            reflexion_result = await self._run_reflexion_analysis(
                evaluation_logs or [], improvement_history or []
            )
            
            # 3. 最終品質チェック
            final_assessment = await self._conduct_final_assessment(
                statement_text, university_info, self_analysis_context
            )
            
            # 4. 差分生成（元テキストとの比較）
            diff_result = None
            if original_text and original_text != statement_text:
                diff_result = await self._generate_final_diff(original_text, statement_text)
            
            # 5. 改善された志望理由書を保存
            save_result = None
            if statement_id:
                save_result = await self._save_final_version(
                    statement_id, statement_text, final_assessment, reflexion_result
                )
            
            return {
                "step": "POLISH",
                "status": "completed",
                "polish": {
                    "revision_history": revision_history,
                    "reflexion_analysis": reflexion_result,
                    "final_assessment": final_assessment,
                    "diff_analysis": diff_result,
                    "save_result": save_result,
                    "completion_metrics": self._calculate_completion_metrics(
                        final_assessment, reflexion_result
                    )
                },
                "recommended_changes": self._extract_final_recommendations(
                    final_assessment, reflexion_result
                ),
                "completion_status": self._determine_completion_status(final_assessment)
            }
            
        except Exception as e:
            logger.error(f"Error in POLISH step: {e}")
            return {
                "step": "POLISH",
                "status": "error",
                "error": str(e),
                "polish": self._fallback_polish_analysis(statement_text)
            }
    
    async def _get_revision_history(self, statement_id: str) -> Dict[str, Any]:
        """ツール#17: リビジョン履歴取得"""
        try:
            result = await list_revisions_tool.ainvoke({"statement_id": statement_id})
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Revision history error: {e}")
            return {"error": str(e)}
    
    async def _run_reflexion_analysis(self, evaluation_logs: List[Dict], 
                                    improvement_history: List[Dict]) -> Dict[str, Any]:
        """ツール#20: リフレクション分析実行"""
        try:
            result = await apply_reflexion_tool.ainvoke({
                "evaluation_logs": evaluation_logs,
                "improvement_history": improvement_history
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Reflexion analysis error: {e}")
            return {"error": str(e)}
    
    async def _generate_final_diff(self, original_text: str, final_text: str) -> Dict[str, Any]:
        """ツール#15: 最終差分生成"""
        try:
            result = await diff_versions_tool.ainvoke({
                "original_text": original_text,
                "revised_text": final_text
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Final diff generation error: {e}")
            return {"error": str(e)}
    
    async def _save_final_version(self, statement_id: str, statement_text: str,
                                final_assessment: Dict, reflexion_result: Dict) -> Dict[str, Any]:
        """ツール#16: 最終版保存"""
        try:
            revision_data = {
                "content": statement_text,
                "changes_summary": "最終仕上げ完了",
                "metadata": {
                    "final_assessment": final_assessment,
                    "reflexion_analysis": reflexion_result,
                    "completion_timestamp": self._get_current_timestamp()
                }
            }
            
            result = await save_revision_tool.ainvoke({
                "statement_id": statement_id,
                "revision_data": revision_data
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Save final version error: {e}")
            return {"error": str(e)}
    
    async def _conduct_final_assessment(self, statement_text: str, university_info: str,
                                      self_analysis_context: str) -> Dict[str, Any]:
        """最終品質評価を実行"""
        try:
            assessment_prompt = f"""{POLISH_PROMPT}

志望理由書（最終版）:
{statement_text}

志望大学情報:
{university_info}

自己分析コンテキスト:
{self_analysis_context}

以下の観点から最終的な品質評価を行ってください：
1. 技術的完成度（文法、語法、構成）
2. 内容の充実度と説得力
3. 大学との適合性
4. 個性と独自性
5. 全体的な印象とインパクト

最終グレードと総合評価を提示してください。
"""
            
            response = await self.llm.ainvoke(assessment_prompt)
            
            # 最終評価の構造化
            assessment = {
                "comprehensive_evaluation": response.content,
                "technical_quality": self._assess_technical_quality(statement_text),
                "content_richness": self._assess_content_richness(statement_text),
                "university_fit": self._assess_university_fit(statement_text, university_info),
                "uniqueness": self._assess_uniqueness(statement_text),
                "overall_impact": self._assess_overall_impact(statement_text),
                "final_scores": self._calculate_final_scores(statement_text),
                "readiness_assessment": self._assess_readiness(statement_text)
            }
            
            return assessment
            
        except Exception as e:
            logger.error(f"Final assessment error: {e}")
            return {"error": str(e)}
    
    def _assess_technical_quality(self, statement_text: str) -> Dict[str, Any]:
        """技術的品質を評価"""
        # 基本的な技術指標
        word_count = len(statement_text.replace(' ', '').replace('\n', ''))
        paragraph_count = len([p for p in statement_text.split('\n\n') if p.strip()])
        sentence_count = len([s for s in statement_text.split('。') if s.strip()])
        
        # 文法的な指標（簡易）
        grammar_issues = self._detect_basic_grammar_issues(statement_text)
        
        return {
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "sentence_count": sentence_count,
            "average_sentence_length": word_count / sentence_count if sentence_count > 0 else 0,
            "grammar_issues_count": len(grammar_issues),
            "structure_score": self._calculate_structure_score(paragraph_count, word_count),
            "technical_grade": self._calculate_technical_grade(grammar_issues, paragraph_count, word_count)
        }
    
    def _assess_content_richness(self, statement_text: str) -> Dict[str, Any]:
        """内容の充実度を評価"""
        # 内容指標
        content_keywords = {
            "specific_examples": ["例えば", "具体的に", "実際に", "〜した結果"],
            "achievements": ["成果", "達成", "成功", "向上", "改善"],
            "learning": ["学んだ", "気づいた", "理解した", "身につけた"],
            "future_plans": ["目標", "計画", "将来", "予定", "目指す"]
        }
        
        content_scores = {}
        for category, keywords in content_keywords.items():
            score = sum(statement_text.count(kw) for kw in keywords)
            content_scores[category] = min(10, score * 2)
        
        return {
            "content_scores": content_scores,
            "richness_level": self._determine_richness_level(content_scores),
            "depth_indicators": self._identify_depth_indicators(statement_text),
            "content_grade": sum(content_scores.values()) / len(content_scores)
        }
    
    def _assess_university_fit(self, statement_text: str, university_info: str) -> Dict[str, Any]:
        """大学適合性を評価"""
        if not university_info:
            return {"fit_score": 7.0, "note": "大学情報が不足しています"}
        
        university_keywords = university_info.split()[:10]
        mention_count = sum(statement_text.count(kw) for kw in university_keywords if len(kw) > 2)
        
        return {
            "university_mentions": mention_count,
            "fit_score": min(10, mention_count * 1.5),
            "specificity_level": "high" if mention_count >= 5 else "medium" if mention_count >= 2 else "low",
            "alignment_grade": "A" if mention_count >= 5 else "B" if mention_count >= 2 else "C"
        }
    
    def _assess_uniqueness(self, statement_text: str) -> Dict[str, Any]:
        """独自性・個性を評価"""
        # 個性的な表現の指標
        personal_indicators = ["私の", "私は", "私が", "私にとって"]
        personal_count = sum(statement_text.count(indicator) for indicator in personal_indicators)
        
        # 具体的な体験の指標
        experience_indicators = ["体験", "経験", "出来事", "エピソード"]
        experience_count = sum(statement_text.count(indicator) for indicator in experience_indicators)
        
        uniqueness_score = min(10, (personal_count + experience_count) * 1.2)
        
        return {
            "personal_expression_count": personal_count,
            "experience_references": experience_count,
            "uniqueness_score": round(uniqueness_score, 1),
            "personality_level": "strong" if uniqueness_score >= 7 else "moderate" if uniqueness_score >= 5 else "weak"
        }
    
    def _assess_overall_impact(self, statement_text: str) -> Dict[str, Any]:
        """全体的なインパクトを評価"""
        # 印象的な表現の検出
        impact_expressions = ["強く", "深く", "心から", "真剣に", "本気で", "必ず"]
        impact_count = sum(statement_text.count(expr) for expr in impact_expressions)
        
        # 文章の結論力
        conclusion_strength = self._assess_conclusion_strength(statement_text)
        
        overall_impact = (impact_count * 1.5 + conclusion_strength) / 2
        
        return {
            "impact_expressions": impact_count,
            "conclusion_strength": conclusion_strength,
            "overall_impact_score": round(min(10, overall_impact), 1),
            "impression_level": "strong" if overall_impact >= 7 else "moderate" if overall_impact >= 5 else "needs_improvement"
        }
    
    def _calculate_final_scores(self, statement_text: str) -> Dict[str, float]:
        """最終スコアを計算"""
        technical = self._assess_technical_quality(statement_text)
        content = self._assess_content_richness(statement_text)
        uniqueness = self._assess_uniqueness(statement_text)
        impact = self._assess_overall_impact(statement_text)
        
        return {
            "technical_score": technical.get("technical_grade", 7.0),
            "content_score": content.get("content_grade", 7.0),
            "uniqueness_score": uniqueness.get("uniqueness_score", 7.0),
            "impact_score": impact.get("overall_impact_score", 7.0),
            "overall_score": (
                technical.get("technical_grade", 7.0) +
                content.get("content_grade", 7.0) +
                uniqueness.get("uniqueness_score", 7.0) +
                impact.get("overall_impact_score", 7.0)
            ) / 4
        }
    
    def _assess_readiness(self, statement_text: str) -> Dict[str, Any]:
        """提出準備度を評価"""
        final_scores = self._calculate_final_scores(statement_text)
        overall_score = final_scores["overall_score"]
        
        readiness_level = "ready" if overall_score >= 8.0 else "nearly_ready" if overall_score >= 7.0 else "needs_improvement"
        
        return {
            "readiness_level": readiness_level,
            "overall_score": round(overall_score, 1),
            "grade": self._assign_final_grade(overall_score),
            "submission_recommendation": self._get_submission_recommendation(readiness_level),
            "final_checklist": self._generate_final_checklist(statement_text)
        }
    
    def _detect_basic_grammar_issues(self, statement_text: str) -> List[str]:
        """基本的な文法問題を検出"""
        issues = []
        
        if "。。" in statement_text:
            issues.append("句点の重複")
        if "、、" in statement_text:
            issues.append("読点の重複")
        if statement_text.count("である") > 0 and statement_text.count("です") > 0:
            issues.append("文体の不統一")
        
        return issues
    
    def _calculate_structure_score(self, paragraph_count: int, word_count: int) -> float:
        """構造スコアを計算"""
        # 理想的な構成：3-5段落、800-1200文字
        paragraph_score = min(10, max(0, 10 - abs(4 - paragraph_count) * 2))
        length_score = min(10, max(0, 10 - abs(1000 - word_count) / 100))
        
        return round((paragraph_score + length_score) / 2, 1)
    
    def _calculate_technical_grade(self, grammar_issues: List, paragraph_count: int, word_count: int) -> float:
        """技術的グレードを計算"""
        structure_score = self._calculate_structure_score(paragraph_count, word_count)
        grammar_penalty = len(grammar_issues) * 0.5
        
        return round(max(5.0, structure_score - grammar_penalty), 1)
    
    def _determine_richness_level(self, content_scores: Dict) -> str:
        """内容の豊富さレベルを決定"""
        avg_score = sum(content_scores.values()) / len(content_scores)
        
        if avg_score >= 7:
            return "rich"
        elif avg_score >= 5:
            return "adequate"
        else:
            return "needs_enrichment"
    
    def _identify_depth_indicators(self, statement_text: str) -> List[str]:
        """深度指標を特定"""
        indicators = []
        
        if "なぜなら" in statement_text:
            indicators.append("理由説明")
        if "その結果" in statement_text:
            indicators.append("因果関係")
        if "例えば" in statement_text:
            indicators.append("具体例")
        if "さらに" in statement_text:
            indicators.append("発展的記述")
        
        return indicators
    
    def _assess_conclusion_strength(self, statement_text: str) -> float:
        """結論部分の強さを評価"""
        conclusion_indicators = ["決意", "決心", "確信", "必ず", "絶対に", "実現"]
        conclusion_count = sum(statement_text.count(indicator) for indicator in conclusion_indicators)
        
        return min(10, conclusion_count * 2.5)
    
    def _assign_final_grade(self, overall_score: float) -> str:
        """最終グレードを割り当て"""
        if overall_score >= 9.0:
            return "A+"
        elif overall_score >= 8.5:
            return "A"
        elif overall_score >= 8.0:
            return "A-"
        elif overall_score >= 7.5:
            return "B+"
        elif overall_score >= 7.0:
            return "B"
        elif overall_score >= 6.5:
            return "B-"
        elif overall_score >= 6.0:
            return "C+"
        else:
            return "C"
    
    def _get_submission_recommendation(self, readiness_level: str) -> str:
        """提出推奨度を取得"""
        recommendations = {
            "ready": "提出準備完了です。自信を持って提出してください。",
            "nearly_ready": "ほぼ完成しています。最終確認後に提出をお勧めします。",
            "needs_improvement": "さらなる改善が必要です。指摘された点を修正してください。"
        }
        
        return recommendations.get(readiness_level, "評価を再確認してください。")
    
    def _generate_final_checklist(self, statement_text: str) -> List[Dict]:
        """最終チェックリストを生成"""
        checklist = []
        
        # 基本要素のチェック
        word_count = len(statement_text.replace(' ', '').replace('\n', ''))
        paragraph_count = len([p for p in statement_text.split('\n\n') if p.strip()])
        
        checklist.append({
            "item": "文字数",
            "status": "ok" if 800 <= word_count <= 1200 else "attention",
            "detail": f"現在: {word_count}文字"
        })
        
        checklist.append({
            "item": "段落構成",
            "status": "ok" if 3 <= paragraph_count <= 5 else "attention",
            "detail": f"現在: {paragraph_count}段落"
        })
        
        # 内容要素のチェック
        has_motivation = any(kw in statement_text for kw in ["動機", "きっかけ", "理由"])
        checklist.append({
            "item": "志望動機",
            "status": "ok" if has_motivation else "attention",
            "detail": "志望動機が明確に記述されているか"
        })
        
        has_experience = any(kw in statement_text for kw in ["体験", "経験", "学んだ"])
        checklist.append({
            "item": "具体的体験",
            "status": "ok" if has_experience else "attention", 
            "detail": "具体的な体験や学びが含まれているか"
        })
        
        has_goals = any(kw in statement_text for kw in ["目標", "将来", "学びたい"])
        checklist.append({
            "item": "将来目標",
            "status": "ok" if has_goals else "attention",
            "detail": "将来の目標や計画が記述されているか"
        })
        
        return checklist
    
    def _calculate_completion_metrics(self, final_assessment: Dict, reflexion_result: Dict) -> Dict[str, Any]:
        """完成度メトリクスを計算"""
        final_scores = final_assessment.get("final_scores", {})
        
        return {
            "completion_percentage": min(100, final_scores.get("overall_score", 7.0) * 10),
            "quality_level": self._determine_quality_level(final_scores.get("overall_score", 7.0)),
            "improvement_progress": self._calculate_improvement_progress(reflexion_result),
            "readiness_status": final_assessment.get("readiness_assessment", {}).get("readiness_level", "needs_improvement")
        }
    
    def _determine_quality_level(self, overall_score: float) -> str:
        """品質レベルを決定"""
        if overall_score >= 8.5:
            return "excellent"
        elif overall_score >= 7.5:
            return "good"
        elif overall_score >= 6.5:
            return "satisfactory"
        else:
            return "needs_improvement"
    
    def _calculate_improvement_progress(self, reflexion_result: Dict) -> str:
        """改善進捗を計算"""
        next_steps = reflexion_result.get("next_steps", [])
        
        if not next_steps:
            return "completed"
        elif len(next_steps) <= 2:
            return "nearly_completed"
        else:
            return "in_progress"
    
    def _extract_final_recommendations(self, final_assessment: Dict, reflexion_result: Dict) -> List[Dict]:
        """最終推奨事項を抽出"""
        recommendations = []
        
        # 品質評価からの推奨事項
        readiness = final_assessment.get("readiness_assessment", {})
        if readiness.get("readiness_level") != "ready":
            recommendations.append({
                "type": "quality_improvement",
                "priority": "high",
                "description": "全体的な品質向上が必要",
                "action": readiness.get("submission_recommendation", "")
            })
        
        # リフレクション分析からの推奨事項
        reflexion_recommendations = reflexion_result.get("recommendations", [])
        for rec in reflexion_recommendations[:2]:  # 上位2件
            recommendations.append({
                "type": "reflexion_based",
                "priority": "medium",
                "description": rec,
                "action": "リフレクション分析に基づく改善"
            })
        
        return recommendations
    
    def _determine_completion_status(self, final_assessment: Dict) -> Dict[str, Any]:
        """完成ステータスを決定"""
        readiness = final_assessment.get("readiness_assessment", {})
        final_scores = final_assessment.get("final_scores", {})
        
        return {
            "status": readiness.get("readiness_level", "needs_improvement"),
            "grade": readiness.get("grade", "C"),
            "score": readiness.get("overall_score", 6.0),
            "message": readiness.get("submission_recommendation", ""),
            "next_action": "submit" if readiness.get("readiness_level") == "ready" else "improve"
        }
    
    def _get_current_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _fallback_polish_analysis(self, statement_text: str) -> Dict[str, Any]:
        """エラー時のフォールバック分析"""
        word_count = len(statement_text.replace(' ', '').replace('\n', ''))
        
        return {
            "basic_assessment": {
                "word_count": word_count,
                "estimated_quality": "medium",
                "completion_level": "partial"
            },
            "general_recommendations": [
                "最終チェックを実施",
                "全体的な品質を確認",
                "提出前の最終確認を推奨"
            ],
            "completion_metrics": {
                "completion_percentage": 75,
                "quality_level": "satisfactory",
                "readiness_status": "needs_review"
            },
            "error_note": "技術的問題により詳細な最終分析が実行できませんでした"
        } 