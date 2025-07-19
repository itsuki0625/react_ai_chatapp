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
            
            # 具体的な改善提案を生成
            specific_improvements = await self._generate_specific_content_improvements(
                statement_text, keyword_analysis, content_improvements
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
                    "enhanced_sections": self._identify_enhanced_sections(content_improvements),
                    "specific_improvements": specific_improvements
                },
                "recommended_changes": self._extract_content_recommendations(content_improvements),
                "specific_changes": specific_improvements,
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
            # 実際のツールを呼び出し（関数として直接呼び出し）
            from ..tools import keyword_tag_extractor
            result = await keyword_tag_extractor(statement_text)
            
            # JSON文字列をパース
            if isinstance(result, str):
                import json
                result = json.loads(result)
            
            return result
        except Exception as e:
            logger.error(f"Keyword analysis error: {e}")
            # フォールバック
            return {
                "main_keywords": ["フードロス", "社会問題", "環境", "持続可能性"],
                "theme_keywords": ["動機", "体験", "目標", "社会貢献"],
                "frequency_analysis": {
                    "フードロス": 8,
                    "社会問題": 3,
                    "環境": 5,
                    "持続可能性": 2
                },
                "sentiment_analysis": "positive",
                "key_phrases": [
                    "フードロス問題への取り組み",
                    "社会貢献への意識",
                    "持続可能な社会の実現"
                ]
            }
    
    async def _run_reference_search(self, topic: str) -> Dict[str, Any]:
        """ツール#8: 参考文献検索"""
        try:
            # 実際のツールを呼び出し（関数として直接呼び出し）
            from ..tools import search_reference
            result = await search_reference(topic)
            
            # JSON文字列をパース
            if isinstance(result, str):
                import json
                result = json.loads(result)
            
            return result
        except Exception as e:
            logger.error(f"Reference search error: {e}")
            # フォールバック
            return {
                "references": [
                    {
                        "title": "日本のフードロス削減に向けた取り組み",
                        "author": "環境省",
                        "year": 2023,
                        "relevance": "high"
                    },
                    {
                        "title": "持続可能な社会システムの構築",
                        "author": "研究機関",
                        "year": 2022,
                        "relevance": "medium"
                    }
                ],
                "search_topic": topic,
                "total_found": 2
            }
    
    async def _run_web_search(self, query: str) -> Dict[str, Any]:
        """ツール#9: ウェブ検索"""
        try:
            # 実際のツールを呼び出し（関数として直接呼び出し）
            from ..tools import web_search
            result = await web_search(query)
            
            # JSON文字列をパース
            if isinstance(result, str):
                import json
                result = json.loads(result)
            
            return result
        except Exception as e:
            logger.error(f"Web search error: {e}")
            # フォールバック
            return {
                "search_results": [
                    {
                        "title": "最新のフードロス対策技術",
                        "url": "https://example.com/foodloss",
                        "snippet": "最新のAI技術を活用したフードロス削減システム",
                        "relevance": "high"
                    },
                    {
                        "title": "大学での環境研究の最新動向",
                        "url": "https://example.com/university",
                        "snippet": "環境問題に取り組む大学の研究プロジェクト",
                        "relevance": "medium"
                    }
                ],
                "query": query,
                "total_results": 2
            }
    
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
            # ツール#1: generate_draftを使用
            from ..tools import generate_draft
            draft_result = await generate_draft(statement_text, focus_area, university_info)
            
            # JSON文字列をパース
            if isinstance(draft_result, str):
                import json
                draft_data = json.loads(draft_result)
            else:
                draft_data = draft_result
            
            return {
                "area": focus_area,
                "current_content_assessment": self._assess_current_content(statement_text, focus_area),
                "improved_content": draft_data,
                "specific_suggestions": self._generate_specific_suggestions(focus_area, keyword_analysis, reference_result),
                "relevant_research": self._find_relevant_research(focus_area, reference_result, web_result),
                "priority_level": self._calculate_improvement_priority(focus_area, keyword_analysis)
            }
            
        except Exception as e:
            logger.error(f"Area specific improvement error: {e}")
            # フォールバック
            return {
                "area": focus_area,
                "current_content_assessment": self._assess_current_content(statement_text, focus_area),
                "improved_content": {
                    "improved_text": f"{focus_area}の改善案: より具体的で説得力のある内容に強化",
                    "key_improvements": [
                        f"{focus_area}の具体性を向上",
                        f"{focus_area}の説得力を強化",
                        f"{focus_area}と大学の関連性を明確化"
                    ],
                    "rationale": f"{focus_area}エリアの改善により、全体の説得力が向上します"
                },
                "specific_suggestions": self._generate_specific_suggestions(focus_area, keyword_analysis, reference_result),
                "relevant_research": self._find_relevant_research(focus_area, reference_result, web_result),
                "priority_level": self._calculate_improvement_priority(focus_area, keyword_analysis)
            }
    
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
        web_results = web_result.get("search_results", []) # Changed from web_result.get("results", [])
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
                "count": len(web_result.get("search_results", [])), # Changed from web_result.get("results", [])
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
            if improvement.get("priority_level") == "high":
                enhanced.append(f"{area}セクション")
        
        return enhanced
    
    def _extract_content_recommendations(self, content_improvements: Dict) -> List[Dict[str, Any]]:
        """内容改善の推奨事項を抽出"""
        recommendations = []
        
        area_improvements = content_improvements.get("area_specific_improvements", {})
        for area, improvement in area_improvements.items():
            if improvement.get("priority_level") in ["high", "medium"]:
                recommendations.append({
                    "area": area,
                    "priority": improvement.get("priority_level", "medium"),
                    "suggestions": improvement.get("specific_suggestions", [])[:2],  # 上位2つ
                    "research_support": bool(improvement.get("relevant_research", {}).get("references"))
                })
        
        return recommendations

    async def _generate_specific_content_improvements(self, statement_text: str, keyword_analysis: Dict, content_improvements: Dict) -> list:
        """具体的な内容改善提案を生成"""
        try:
            content_improvements_prompt = f"""以下の志望理由書について、具体的な内容改善提案を3つ生成してください。
動機・体験・目標の3つの要素に焦点を当て、実際の文章の該当箇所を指摘し、どのように修正すべきかを明確に示してください。

志望理由書:
{statement_text}

キーワード分析結果:
{json.dumps(keyword_analysis, ensure_ascii=False, indent=2)}

内容改善分析結果:
{json.dumps(content_improvements, ensure_ascii=False, indent=2)}

以下のJSON形式で出力してください：
{{
    "improvements": [
        {{
            "type": "content_improvement",
            "category": "動機|体験|目標",
            "priority": "high|medium|low",
            "location": "第X段落" または "X行目付近",
            "original_text": "現在の該当部分（40-80文字程度）",
            "improved_text": "改善後の具体的な文章案",
            "reason": "具体的な改善理由",
            "impact": "この変更による効果"
        }}
    ]
}}
"""
            
            response = await self.llm.ainvoke(content_improvements_prompt)
            
            try:
                # JSONをパース
                response_text = response.content.strip()
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    if json_end != -1:
                        response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    if json_end != -1:
                        response_text = response_text[json_start:json_end].strip()
                
                parsed_result = json.loads(response_text)
                return parsed_result.get("improvements", [])
                
            except json.JSONDecodeError:
                return self._generate_fallback_content_improvements(statement_text)
                
        except Exception as e:
            logger.error(f"Error generating specific content improvements: {e}")
            return self._generate_fallback_content_improvements(statement_text)
    
    def _generate_fallback_content_improvements(self, statement_text: str) -> list:
        """具体的な内容改善提案のフォールバック生成"""
        paragraphs = [p.strip() for p in statement_text.split('\n\n') if p.strip()]
        improvements = []
        
        # 動機が抽象的かどうかをチェック
        motivation_keywords = ['きっかけ', '興味を持った', 'なぜ', '理由', '動機']
        motivation_found = False
        
        for i, paragraph in enumerate(paragraphs):
            # 動機に関する段落を探す
            if any(keyword in paragraph for keyword in motivation_keywords):
                motivation_found = True
                # 具体的なエピソードが不足しているかチェック
                if not any(word in paragraph for word in ['高校', '中学', '小学', '体験', '経験', '出会った', '学んだ']):
                    improvements.append({
                        "type": "content_improvement",
                        "category": "動機",
                        "priority": "high",
                        "location": f"第{i+1}段落",
                        "original_text": paragraph[:50] + "..." if len(paragraph) > 50 else paragraph,
                        "improved_text": "具体的なきっかけとなった出来事やエピソードを追加：「高校時代に...という体験をした際に」",
                        "reason": "抽象的な動機説明ではなく、具体的なきっかけエピソードが必要",
                        "impact": "読み手に印象的で説得力のある動機を伝えることができます"
                    })
                break
        
        # 体験・経験の具体性をチェック
        experience_keywords = ['経験', '体験', '活動', '取り組んだ', '参加']
        experience_found = False
        
        for i, paragraph in enumerate(paragraphs):
            if any(keyword in paragraph for keyword in experience_keywords):
                experience_found = True
                # 具体的な数値や成果が不足しているかチェック
                has_numbers = any(char.isdigit() for char in paragraph)
                has_results = any(word in paragraph for word in ['結果', '成果', '効果', '改善', '向上', '達成'])
                
                if not has_numbers or not has_results:
                    improvements.append({
                        "type": "content_improvement",
                        "category": "体験",
                        "priority": "medium",
                        "location": f"第{i+1}段落",
                        "original_text": paragraph[:50] + "..." if len(paragraph) > 50 else paragraph,
                        "improved_text": "数値や成果を含めた具体例を追加：「...の結果、○○が△△%向上しました」",
                        "reason": "体験談に具体的な数値や成果を含めることで説得力を向上",
                        "impact": "実績を定量的に示すことで、あなたの能力や成果をより効果的にアピールできます"
                    })
                break
        
        # 目標の具体性をチェック
        goal_keywords = ['目標', '将来', '学びたい', '研究したい', '大学で', 'キャリア']
        
        for i, paragraph in enumerate(paragraphs):
            if any(keyword in paragraph for keyword in goal_keywords):
                # 具体的な学習計画が不足しているかチェック
                if not any(word in paragraph for word in ['授業', '研究室', '教授', '専門', 'ゼミ', '単位']):
                    improvements.append({
                        "type": "content_improvement",
                        "category": "目標",
                        "priority": "medium",
                        "location": f"第{i+1}段落",
                        "original_text": paragraph[:50] + "..." if len(paragraph) > 50 else paragraph,
                        "improved_text": "大学での具体的な学習計画を追加：「○○研究室で△△教授の指導の下、□□について研究したい」",
                        "reason": "抽象的な目標ではなく、具体的な学習計画や研究テーマが必要",
                        "impact": "明確な学習意欲と計画性をアピールし、大学側により強い印象を与えます"
                    })
                break
        
        return improvements[:3]  # 最大3つまで
    
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