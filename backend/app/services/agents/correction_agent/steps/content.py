import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from ..prompts import CONTENT_PROMPT
from ..tools import (
    generate_draft_tool,
    search_reference_tool,
    web_search_tool,
    keyword_tag_extractor_tool
)

logger = logging.getLogger(__name__)

class ContentStepAgent:
    """内容の肉付け・説得力強化を行うステップエージェント"""
    
    def __init__(self, temperature: float = 0.6):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            max_tokens=1400
        )
        # 統合設計書のマッピングに従ったツール
        self.tools = [
            generate_draft_tool,       # ツール#1
            search_reference_tool,     # ツール#8
            web_search_tool,          # ツール#9
            keyword_tag_extractor_tool # ツール#14
        ]
    
    async def execute(self, statement_text: str, university_info: str = "",
                     self_analysis_context: str = "", focus_areas: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        CONTENTステップを実行
        統合設計書に従い、4つのツールを使用して内容強化を実施
        """
        try:
            logger.info("Starting CONTENT step with 4 tools")
            
            # キーワード分析を最初に実行
            keyword_analysis = await self._run_keyword_analysis(statement_text)
            
            # 並列実行でリサーチツールを呼び出し
            research_tasks = []
            
            # 参考文献検索
            main_keywords = self._extract_main_keywords(keyword_analysis)
            if main_keywords:
                research_tasks.append(self._run_reference_search(main_keywords[0]))
            
            # ウェブ検索（最新動向）
            if university_info:
                research_tasks.append(self._run_web_search(f"{university_info} 最新動向"))
            
            # 並列実行
            research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
            
            reference_result = research_results[0] if len(research_results) > 0 and not isinstance(research_results[0], Exception) else {}
            web_result = research_results[1] if len(research_results) > 1 and not isinstance(research_results[1], Exception) else {}
            
            # 内容改善を実行
            content_improvements = await self._generate_content_improvements(
                statement_text, keyword_analysis, reference_result, web_result, 
                university_info, focus_areas or ["動機", "体験", "目標"]
            )
            
            return {
                "step": "CONTENT",
                "status": "completed",
                "content": {
                    "keyword_analysis": keyword_analysis,
                    "research_results": {
                        "references": reference_result,
                        "web_insights": web_result
                    },
                    "improvements": content_improvements,
                    "enhanced_sections": self._identify_enhanced_sections(content_improvements)
                },
                "recommended_changes": self._extract_content_recommendations(content_improvements),
                "next_recommended_steps": ["EXPRESSION", "COHERENCE"]
            }
            
        except Exception as e:
            logger.error(f"Error in CONTENT step: {e}")
            return {
                "step": "CONTENT",
                "status": "error",
                "error": str(e),
                "content": self._fallback_content_analysis(statement_text)
            }
    
    async def _run_keyword_analysis(self, statement_text: str) -> Dict[str, Any]:
        """ツール#14: キーワード抽出・分析"""
        try:
            result = await keyword_tag_extractor_tool.ainvoke({"text": statement_text})
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Keyword analysis error: {e}")
            return {"error": str(e)}
    
    async def _run_reference_search(self, topic: str) -> Dict[str, Any]:
        """ツール#8: 参考文献検索"""
        try:
            result = await search_reference_tool.ainvoke({
                "topic": topic,
                "limit": 3
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Reference search error: {e}")
            return {"error": str(e)}
    
    async def _run_web_search(self, query: str) -> Dict[str, Any]:
        """ツール#9: ウェブ検索"""
        try:
            result = await web_search_tool.ainvoke({
                "query": query,
                "limit": 3
            })
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {"error": str(e)}
    
    async def _generate_content_improvements(self, statement_text: str, keyword_analysis: Dict,
                                           reference_result: Dict, web_result: Dict,
                                           university_info: str, focus_areas: List[str]) -> Dict[str, Any]:
        """内容改善案を生成"""
        try:
            improvement_prompt = f"""{CONTENT_PROMPT}

現在の志望理由書:
{statement_text}

キーワード分析結果:
{json.dumps(keyword_analysis, ensure_ascii=False, indent=2)}

参考文献情報:
{json.dumps(reference_result, ensure_ascii=False, indent=2)}

最新動向情報:
{json.dumps(web_result, ensure_ascii=False, indent=2)}

志望大学情報:
{university_info}

改善対象エリア: {', '.join(focus_areas)}

以下の観点から内容を強化してください：
1. テーマの明確化と深掘り
2. 具体的なエピソードの強化
3. 大学との関連性の向上
4. 説得力のある根拠の追加
5. 参考文献・最新動向の活用

各セクションの改善案を具体的に提示してください。
"""
            
            response = await self.llm.ainvoke(improvement_prompt)
            
            # 改善案を各フォーカスエリアに展開
            improvements = {}
            for area in focus_areas:
                area_improvement = await self._generate_area_specific_improvement(
                    statement_text, area, keyword_analysis, reference_result, web_result, university_info
                )
                improvements[area] = area_improvement
            
            return {
                "overall_assessment": response.content,
                "area_specific_improvements": improvements,
                "research_integration": self._suggest_research_integration(reference_result, web_result),
                "content_depth_score": self._calculate_content_depth(keyword_analysis),
                "university_connection_score": self._calculate_university_connection(statement_text, university_info),
                "recommendations": self._extract_improvement_recommendations(response.content)
            }
            
        except Exception as e:
            logger.error(f"Content improvement generation error: {e}")
            return {"error": str(e)}
    
    async def _generate_area_specific_improvement(self, statement_text: str, focus_area: str,
                                                keyword_analysis: Dict, reference_result: Dict,
                                                web_result: Dict, university_info: str) -> Dict[str, Any]:
        """特定エリアの改善案を生成"""
        try:
            # ツール#1を使用して段落深掘り
            draft_result = await generate_draft_tool.ainvoke({
                "current_text": statement_text,
                "focus_area": focus_area,
                "university_info": university_info
            })
            
            draft_data = json.loads(draft_result) if isinstance(draft_result, str) else draft_result
            
            return {
                "area": focus_area,
                "current_content_assessment": self._assess_current_content(statement_text, focus_area),
                "generated_improvements": draft_data,
                "specific_suggestions": self._generate_specific_suggestions(focus_area, keyword_analysis, reference_result),
                "research_support": self._find_relevant_research(focus_area, reference_result, web_result),
                "improvement_priority": self._calculate_improvement_priority(focus_area, keyword_analysis)
            }
            
        except Exception as e:
            logger.error(f"Area-specific improvement error for {focus_area}: {e}")
            return {"area": focus_area, "error": str(e)}
    
    def _extract_main_keywords(self, keyword_analysis: Dict) -> List[str]:
        """主要キーワードを抽出"""
        keywords = keyword_analysis.get("keywords", [])
        main_themes = keyword_analysis.get("main_themes", [])
        
        # 重要度順でソート
        sorted_keywords = sorted(keywords, key=lambda x: x.get("importance", 0), reverse=True)
        
        # 上位キーワードとメインテーマを結合
        result = main_themes[:2]  # 上位2つのテーマ
        result.extend([kw.get("word", "") for kw in sorted_keywords[:3]])  # 上位3つのキーワード
        
        return [kw for kw in result if kw]
    
    def _assess_current_content(self, statement_text: str, focus_area: str) -> Dict[str, Any]:
        """現在の内容を評価"""
        # 簡易的な内容評価
        area_keywords = {
            "動機": ["きっかけ", "理由", "なぜ", "動機", "興味"],
            "体験": ["経験", "体験", "学んだ", "取り組んだ", "活動"],
            "目標": ["目標", "目的", "将来", "学びたい", "研究したい"]
        }
        
        relevant_keywords = area_keywords.get(focus_area, [])
        keyword_count = sum(statement_text.count(kw) for kw in relevant_keywords)
        
        return {
            "area": focus_area,
            "keyword_density": keyword_count / len(statement_text) * 1000 if statement_text else 0,
            "content_length": len([s for s in statement_text.split('。') if focus_area in s]),
            "specificity_score": min(10, keyword_count * 2),
            "needs_improvement": keyword_count < 2
        }
    
    def _generate_specific_suggestions(self, focus_area: str, keyword_analysis: Dict, reference_result: Dict) -> List[str]:
        """具体的な改善提案を生成"""
        suggestions = []
        
        # エリア別の基本提案
        area_suggestions = {
            "動機": [
                "具体的なきっかけエピソードを追加",
                "なぜその分野に興味を持ったかを明確化",
                "動機の根拠を強化"
            ],
            "体験": [
                "経験から得た学びを具体化",
                "数値や成果を含めた具体例を追加",
                "体験の意義を明確化"
            ],
            "目標": [
                "大学での具体的な学習計画を追加",
                "将来のキャリア目標を明確化",
                "目標達成のための具体的な行動計画を記述"
            ]
        }
        
        suggestions.extend(area_suggestions.get(focus_area, []))
        
        # 参考文献を活用した提案
        if reference_result.get("references"):
            suggestions.append("関連する研究事例を引用して説得力を向上")
        
        # キーワード分析に基づく提案
        if keyword_analysis.get("keyword_density", 0) < 0.1:
            suggestions.append("専門用語を適切に使用して深度を向上")
        
        return suggestions
    
    def _find_relevant_research(self, focus_area: str, reference_result: Dict, web_result: Dict) -> Dict[str, Any]:
        """関連する研究・情報を特定"""
        relevant_research = {
            "references": [],
            "web_insights": [],
            "applicability": "medium"
        }
        
        # 参考文献から関連情報を抽出
        references = reference_result.get("references", [])
        for ref in references:
            if any(keyword in ref.get("title", "").lower() for keyword in [focus_area, "education", "学習"]):
                relevant_research["references"].append({
                    "title": ref.get("title", ""),
                    "relevance": "high",
                    "usage_suggestion": f"{focus_area}の部分で引用可能"
                })
        
        # ウェブ情報から関連情報を抽出
        web_results = web_result.get("results", [])
        for result in web_results:
            if focus_area in result.get("snippet", ""):
                relevant_research["web_insights"].append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "relevance": "medium"
                })
        
        return relevant_research
    
    def _suggest_research_integration(self, reference_result: Dict, web_result: Dict) -> Dict[str, Any]:
        """研究情報の統合提案"""
        return {
            "reference_integration": {
                "count": len(reference_result.get("references", [])),
                "suggestion": "関連する研究を1-2件引用して学問的深さを向上",
                "placement": "各主要論点の根拠として活用"
            },
            "current_trends": {
                "count": len(web_result.get("results", [])),
                "suggestion": "最新動向を踏まえた将来性をアピール",
                "placement": "目標設定部分で最新情報を活用"
            }
        }
    
    def _calculate_content_depth(self, keyword_analysis: Dict) -> float:
        """内容の深さスコアを計算"""
        keyword_count = len(keyword_analysis.get("keywords", []))
        theme_count = len(keyword_analysis.get("main_themes", []))
        density = keyword_analysis.get("keyword_density", 0)
        
        # 深度スコア計算（0-10）
        depth_score = min(10, (keyword_count * 0.5) + (theme_count * 1.5) + (density * 20))
        return round(depth_score, 1)
    
    def _calculate_university_connection(self, statement_text: str, university_info: str) -> float:
        """大学との関連度スコアを計算"""
        if not university_info:
            return 5.0
        
        # 大学名や特徴的な語句の出現回数
        university_keywords = university_info.split()[:5]  # 最初の5語を取得
        connection_count = sum(statement_text.count(kw) for kw in university_keywords)
        
        # 関連度スコア（0-10）
        connection_score = min(10, connection_count * 2)
        return round(connection_score, 1)
    
    def _calculate_improvement_priority(self, focus_area: str, keyword_analysis: Dict) -> str:
        """改善優先度を計算"""
        area_keywords = keyword_analysis.get("keywords", [])
        area_coverage = sum(1 for kw in area_keywords if focus_area in kw.get("category", ""))
        
        if area_coverage < 2:
            return "high"
        elif area_coverage < 4:
            return "medium"
        else:
            return "low"
    
    def _extract_improvement_recommendations(self, response_content: str) -> List[str]:
        """改善推奨事項を抽出"""
        # 実際の実装では、LLM応答から構造化された推奨事項を抽出
        return [
            "具体的なエピソードを追加して説得力を向上",
            "専門用語を適切に使用して学問的深さを向上",
            "大学との関連性をより明確に記述",
            "参考文献を活用して根拠を強化"
        ]
    
    def _identify_enhanced_sections(self, content_improvements: Dict) -> List[str]:
        """強化されたセクションを特定"""
        enhanced = []
        
        area_improvements = content_improvements.get("area_specific_improvements", {})
        for area, improvement in area_improvements.items():
            if improvement.get("improvement_priority") == "high":
                enhanced.append(f"{area}セクション")
        
        return enhanced
    
    def _extract_content_recommendations(self, content_improvements: Dict) -> List[Dict[str, Any]]:
        """内容改善の推奨事項を抽出"""
        recommendations = []
        
        area_improvements = content_improvements.get("area_specific_improvements", {})
        for area, improvement in area_improvements.items():
            if improvement.get("improvement_priority") in ["high", "medium"]:
                recommendations.append({
                    "area": area,
                    "priority": improvement.get("improvement_priority", "medium"),
                    "suggestions": improvement.get("specific_suggestions", [])[:2],  # 上位2つ
                    "research_support": bool(improvement.get("research_support", {}).get("references"))
                })
        
        return recommendations
    
    def _fallback_content_analysis(self, statement_text: str) -> Dict[str, Any]:
        """エラー時のフォールバック分析"""
        word_count = len(statement_text.replace(' ', '').replace('\n', ''))
        
        return {
            "basic_assessment": {
                "word_count": word_count,
                "estimated_depth": "medium" if word_count > 600 else "shallow",
                "improvement_areas": ["動機", "体験", "目標"]
            },
            "general_suggestions": [
                "具体的な体験談を追加",
                "動機をより明確に記述",
                "将来の目標を具体化"
            ],
            "error_note": "詳細な分析は技術的問題により実行できませんでした"
        } 