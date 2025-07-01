import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from ..prompts import COHERENCE_PROMPT
from ..tools import evaluate_draft_tool

logger = logging.getLogger(__name__)

class CoherenceStepAgent:
    """一貫性・整合性確認を行うステップエージェント"""
    
    def __init__(self, temperature: float = 0.2):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            max_tokens=1000
        )
        # 統合設計書のマッピングに従ったツール
        self.tools = [
            evaluate_draft_tool  # ツール#3（一貫性重視の評価）
        ]
    
    async def execute(self, statement_text: str, university_info: str = "",
                     self_analysis_context: str = "", **kwargs) -> Dict[str, Any]:
        """
        COHERENCEステップを実行
        統合設計書に従い、evaluate_draftツールを使用して一貫性確認を実施
        """
        try:
            logger.info("Starting COHERENCE step with evaluate_draft tool")
            
            # 一貫性重視の評価を実行
            coherence_evaluation = await self._run_coherence_evaluation(
                statement_text, university_info
            )
            
            # 一貫性の詳細分析
            detailed_analysis = await self._analyze_coherence_details(
                statement_text, coherence_evaluation, university_info, self_analysis_context
            )
            
            return {
                "step": "COHERENCE",
                "status": "completed",
                "coherence": {
                    "evaluation": coherence_evaluation,
                    "detailed_analysis": detailed_analysis,
                    "consistency_scores": self._calculate_consistency_scores(detailed_analysis),
                    "flow_assessment": self._assess_logical_flow(statement_text),
                    "theme_coherence": self._assess_theme_coherence(statement_text, detailed_analysis)
                },
                "recommended_changes": self._extract_coherence_recommendations(detailed_analysis),
                "next_recommended_steps": ["POLISH"] if detailed_analysis.get("overall_coherence_score", 7.0) >= 7.0 else ["STRUCTURE", "POLISH"]
            }
            
        except Exception as e:
            logger.error(f"Error in COHERENCE step: {e}")
            return {
                "step": "COHERENCE",
                "status": "error",
                "error": str(e),
                "coherence": self._fallback_coherence_analysis(statement_text)
            }
    
    async def _run_coherence_evaluation(self, statement_text: str, university_info: str) -> Dict[str, Any]:
        """ツール#3: 一貫性重視の評価実行"""
        try:
            result = await evaluate_draft_tool.ainvoke({
                "text": statement_text,
                "university_info": university_info,
                "rubric_type": "coherence_focused"  # 一貫性重視の評価基準
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Coherence evaluation error: {e}")
            return {"error": str(e)}
    
    async def _analyze_coherence_details(self, statement_text: str, evaluation_result: Dict,
                                        university_info: str, self_analysis_context: str) -> Dict[str, Any]:
        """一貫性の詳細分析を実行"""
        try:
            analysis_prompt = f"""{COHERENCE_PROMPT}

志望理由書:
{statement_text}

基本評価結果:
{json.dumps(evaluation_result, ensure_ascii=False, indent=2)}

志望大学情報:
{university_info}

自己分析コンテキスト:
{self_analysis_context}

以下の観点から一貫性を詳細に分析してください：
1. 論理的流れの一貫性
2. テーマの一貫性
3. 議論の強さと整合性
4. 自己分析との整合性
5. 大学志望理由との整合性

具体的な不整合点と改善案を提示してください。
"""
            
            response = await self.llm.ainvoke(analysis_prompt)
            
            # 詳細分析結果の構造化
            analysis = {
                "comprehensive_analysis": response.content,
                "logical_flow_coherence": self._analyze_logical_flow(statement_text),
                "theme_coherence": self._analyze_theme_consistency(statement_text),
                "argument_strength": self._analyze_argument_strength(statement_text, evaluation_result),
                "self_analysis_alignment": self._analyze_self_analysis_alignment(statement_text, self_analysis_context),
                "university_alignment": self._analyze_university_alignment(statement_text, university_info),
                "inconsistency_points": self._identify_inconsistencies(statement_text, evaluation_result),
                "overall_coherence_score": self._calculate_overall_coherence_score(evaluation_result)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Detailed coherence analysis error: {e}")
            return {"error": str(e)}
    
    def _analyze_logical_flow(self, statement_text: str) -> Dict[str, Any]:
        """論理的流れを分析"""
        paragraphs = [p.strip() for p in statement_text.split('\n\n') if p.strip()]
        
        # 論理的接続語の検出
        logical_connectors = ['そのため', 'したがって', 'このように', 'また', 'さらに', 'しかし', 'ただし', 'なぜなら']
        connector_count = sum(statement_text.count(conn) for conn in logical_connectors)
        
        # 段落間の論理的つながりを評価
        flow_score = min(10, 5 + (connector_count * 1.5))
        
        return {
            "paragraph_count": len(paragraphs),
            "logical_connectors_count": connector_count,
            "flow_score": round(flow_score, 1),
            "transition_quality": "good" if connector_count >= 3 else "needs_improvement",
            "recommendations": self._generate_flow_recommendations(connector_count, len(paragraphs))
        }
    
    def _analyze_theme_consistency(self, statement_text: str) -> Dict[str, Any]:
        """テーマの一貫性を分析"""
        # 主要テーマキーワードの検出
        theme_keywords = {
            "motivation": ["動機", "きっかけ", "興味", "関心", "理由"],
            "experience": ["経験", "体験", "学んだ", "取り組んだ", "活動"],
            "goals": ["目標", "目的", "将来", "学びたい", "研究したい"],
            "university": ["大学", "学部", "学科", "研究室", "教授"]
        }
        
        theme_coverage = {}
        for theme, keywords in theme_keywords.items():
            coverage = sum(statement_text.count(kw) for kw in keywords)
            theme_coverage[theme] = coverage
        
        # テーマバランスの評価
        total_coverage = sum(theme_coverage.values())
        balance_score = 10 - (max(theme_coverage.values()) - min(theme_coverage.values())) if total_coverage > 0 else 5
        
        return {
            "theme_coverage": theme_coverage,
            "total_theme_mentions": total_coverage,
            "balance_score": round(max(0, balance_score), 1),
            "dominant_theme": max(theme_coverage.items(), key=lambda x: x[1])[0] if theme_coverage else "unknown",
            "theme_consistency": "high" if balance_score >= 7 else "medium" if balance_score >= 5 else "low"
        }
    
    def _analyze_argument_strength(self, statement_text: str, evaluation_result: Dict) -> Dict[str, Any]:
        """議論の強さを分析"""
        coherence_score = evaluation_result.get("coherence_score", 70)
        overall_score = evaluation_result.get("overall_score", 75)
        
        # 具体例の有無
        concrete_indicators = ["例えば", "具体的に", "実際に", "〜した結果", "数値", "％"]
        concrete_count = sum(statement_text.count(indicator) for indicator in concrete_indicators)
        
        # 根拠の強さ
        evidence_strength = min(10, concrete_count * 2)
        
        return {
            "coherence_score": coherence_score,
            "overall_score": overall_score,
            "concrete_examples_count": concrete_count,
            "evidence_strength": round(evidence_strength, 1),
            "argument_quality": "strong" if evidence_strength >= 6 else "moderate" if evidence_strength >= 3 else "weak",
            "improvement_areas": self._identify_argument_weaknesses(concrete_count, coherence_score)
        }
    
    def _analyze_self_analysis_alignment(self, statement_text: str, self_analysis_context: str) -> Dict[str, Any]:
        """自己分析との整合性を分析"""
        if not self_analysis_context:
            return {"alignment_score": 7.0, "note": "自己分析コンテキストが提供されていません"}
        
        # 簡易的な整合性チェック
        context_keywords = self_analysis_context.split()[:10]  # 最初の10語
        alignment_count = sum(statement_text.count(kw) for kw in context_keywords if len(kw) > 2)
        
        alignment_score = min(10, alignment_count * 1.5)
        
        return {
            "alignment_score": round(alignment_score, 1),
            "matched_keywords": alignment_count,
            "consistency_level": "high" if alignment_score >= 7 else "medium" if alignment_score >= 5 else "low",
            "recommendations": ["自己分析結果をより具体的に反映"] if alignment_score < 6 else []
        }
    
    def _analyze_university_alignment(self, statement_text: str, university_info: str) -> Dict[str, Any]:
        """大学志望理由との整合性を分析"""
        if not university_info:
            return {"alignment_score": 7.0, "note": "大学情報が提供されていません"}
        
        # 大学関連キーワードの言及
        university_keywords = university_info.split()[:8]  # 最初の8語
        mention_count = sum(statement_text.count(kw) for kw in university_keywords if len(kw) > 2)
        
        alignment_score = min(10, mention_count * 2)
        
        return {
            "alignment_score": round(alignment_score, 1),
            "university_mentions": mention_count,
            "specificity_level": "high" if mention_count >= 3 else "medium" if mention_count >= 1 else "low",
            "recommendations": ["大学の特色をより具体的に言及"] if mention_count < 2 else []
        }
    
    def _identify_inconsistencies(self, statement_text: str, evaluation_result: Dict) -> list:
        """不整合点を特定"""
        inconsistencies = []
        
        # 評価スコアから不整合を推定
        coherence_score = evaluation_result.get("coherence_score", 70)
        if coherence_score < 70:
            inconsistencies.append({
                "type": "logical_flow",
                "description": "論理的流れに改善の余地があります",
                "severity": "medium",
                "suggestion": "段落間の接続を強化してください"
            })
        
        # 文章の長さの不均衡
        paragraphs = [p.strip() for p in statement_text.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            lengths = [len(p) for p in paragraphs]
            if max(lengths) > min(lengths) * 3:
                inconsistencies.append({
                    "type": "balance",
                    "description": "段落の長さに大きな偏りがあります",
                    "severity": "low",
                    "suggestion": "段落の分量バランスを調整してください"
                })
        
        return inconsistencies
    
    def _calculate_overall_coherence_score(self, evaluation_result: Dict) -> float:
        """総合一貫性スコアを計算"""
        coherence_score = evaluation_result.get("coherence_score", 70)
        overall_score = evaluation_result.get("overall_score", 75)
        
        # 一貫性を重視したスコア計算
        weighted_score = (coherence_score * 0.7) + (overall_score * 0.3)
        
        return round(weighted_score / 10, 1)  # 10点満点に変換
    
    def _calculate_consistency_scores(self, detailed_analysis: Dict) -> Dict[str, float]:
        """一貫性スコアを計算"""
        return {
            "logical_flow": detailed_analysis.get("logical_flow_coherence", {}).get("flow_score", 7.0),
            "theme_consistency": detailed_analysis.get("theme_coherence", {}).get("balance_score", 7.0),
            "argument_strength": detailed_analysis.get("argument_strength", {}).get("evidence_strength", 7.0),
            "self_analysis_alignment": detailed_analysis.get("self_analysis_alignment", {}).get("alignment_score", 7.0),
            "university_alignment": detailed_analysis.get("university_alignment", {}).get("alignment_score", 7.0),
            "overall_coherence": detailed_analysis.get("overall_coherence_score", 7.0)
        }
    
    def _assess_logical_flow(self, statement_text: str) -> Dict[str, Any]:
        """論理的流れを評価"""
        flow_analysis = self._analyze_logical_flow(statement_text)
        
        return {
            "flow_quality": flow_analysis.get("transition_quality", "needs_improvement"),
            "connector_usage": flow_analysis.get("logical_connectors_count", 0),
            "flow_score": flow_analysis.get("flow_score", 5.0),
            "recommendations": flow_analysis.get("recommendations", [])
        }
    
    def _assess_theme_coherence(self, statement_text: str, detailed_analysis: Dict) -> Dict[str, Any]:
        """テーマの一貫性を評価"""
        theme_analysis = detailed_analysis.get("theme_coherence", {})
        
        return {
            "consistency_level": theme_analysis.get("theme_consistency", "medium"),
            "balance_score": theme_analysis.get("balance_score", 5.0),
            "dominant_theme": theme_analysis.get("dominant_theme", "unknown"),
            "coverage_analysis": theme_analysis.get("theme_coverage", {})
        }
    
    def _generate_flow_recommendations(self, connector_count: int, paragraph_count: int) -> list:
        """流れの改善提案を生成"""
        recommendations = []
        
        if connector_count < 2:
            recommendations.append("論理的接続語を追加して段落間のつながりを強化")
        
        if paragraph_count < 3:
            recommendations.append("内容を適切に段落分けして構造を明確化")
        elif paragraph_count > 6:
            recommendations.append("段落数を整理して読みやすさを向上")
        
        return recommendations
    
    def _identify_argument_weaknesses(self, concrete_count: int, coherence_score: int) -> list:
        """議論の弱点を特定"""
        weaknesses = []
        
        if concrete_count < 2:
            weaknesses.append("具体例や実体験を追加")
        
        if coherence_score < 70:
            weaknesses.append("論理的一貫性の向上")
        
        return weaknesses
    
    def _extract_coherence_recommendations(self, detailed_analysis: Dict) -> list:
        """一貫性改善の推奨事項を抽出"""
        recommendations = []
        
        # 論理的流れの改善
        flow_recommendations = detailed_analysis.get("logical_flow_coherence", {}).get("recommendations", [])
        recommendations.extend(flow_recommendations)
        
        # 議論の強化
        argument_areas = detailed_analysis.get("argument_strength", {}).get("improvement_areas", [])
        recommendations.extend(argument_areas)
        
        # 自己分析との整合性
        self_analysis_recs = detailed_analysis.get("self_analysis_alignment", {}).get("recommendations", [])
        recommendations.extend(self_analysis_recs)
        
        # 大学との整合性
        university_recs = detailed_analysis.get("university_alignment", {}).get("recommendations", [])
        recommendations.extend(university_recs)
        
        return recommendations[:5]  # 上位5件
    
    def _fallback_coherence_analysis(self, statement_text: str) -> Dict[str, Any]:
        """エラー時のフォールバック分析"""
        paragraphs = len([p for p in statement_text.split('\n\n') if p.strip()])
        
        return {
            "basic_assessment": {
                "paragraph_count": paragraphs,
                "estimated_coherence": "medium",
                "basic_structure": "present" if paragraphs >= 3 else "needs_improvement"
            },
            "general_recommendations": [
                "論理的流れを確認",
                "テーマの一貫性をチェック",
                "段落間の接続を強化"
            ],
            "consistency_scores": {
                "logical_flow": 6.0,
                "theme_consistency": 6.0,
                "overall_coherence": 6.0
            },
            "error_note": "技術的問題により詳細な一貫性分析が実行できませんでした"
        } 