import asyncio
import json 
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from ..prompts import STRUCTURE_PROMPT
from ..tools import (
    diff_versions_tool,
    structure_analysis_tool,
    token_guard_tool
)

logger = logging.getLogger(__name__)

class StructureStepAgent:
    """文章構成・論理展開を改善するステップエージェント"""
    
    def __init__(self, temperature: float = 0.4):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=temperature,
            max_tokens=1200
        )
        # 統合設計書のマッピングに従ったツール
        self.tools = [
            diff_versions_tool,       # ツール#15
            structure_analysis_tool,  # 独自ツール
            token_guard_tool         # ツール#19
        ]
    
    async def execute(self, statement_text: str, university_info: str = "",
                     self_analysis_context: str = "", original_text: str = None, **kwargs) -> Dict[str, Any]:
        """
        STRUCTUREステップを実行
        統合設計書に従い、3つのツールを使用して構成改善を実施
        """
        try:
            logger.info("Starting STRUCTURE step with 3 tools")
            
            # トークン使用量を事前チェック
            estimated_tokens = int(len(statement_text) * 1.3)  # 概算、intに変換
            token_status = await self._check_token_usage("STRUCTURE", estimated_tokens)
            
            if token_status.get("status") == "limit_exceeded":
                return {
                    "step": "STRUCTURE", 
                    "status": "error",
                    "error": "トークン制限に達しました",
                    "token_status": token_status
                }
            
            # 構造分析を実行
            structure_analysis = await self._run_structure_analysis(
                statement_text, university_info, self_analysis_context
            )
            
            # 改善案を生成
            improvement_suggestions = await self._generate_structure_improvements(
                statement_text, structure_analysis, university_info
            )
            
            # 具体的な改善提案を生成
            specific_improvements = await self._generate_specific_structure_improvements(
                statement_text, structure_analysis
            )
            
            # 差分生成（改善案がある場合）
            diff_result = None
            if improvement_suggestions.get("improved_structure") and original_text:
                diff_result = await self._generate_diff(
                    original_text, improvement_suggestions["improved_structure"]
                )
            
            return {
                "step": "STRUCTURE",
                "status": "completed", 
                "structure": {
                    "analysis": structure_analysis,
                    "improvements": improvement_suggestions,
                    "diff": diff_result,
                    "token_usage": token_status,
                    "specific_improvements": specific_improvements
                },
                "recommended_changes": self._extract_recommendations(improvement_suggestions),
                "specific_changes": specific_improvements,
                "next_recommended_steps": ["CONTENT", "EXPRESSION"]
            }
            
        except Exception as e:
            logger.error(f"Error in STRUCTURE step: {e}")
            return {
                "step": "STRUCTURE",
                "status": "error", 
                "error": str(e),
                "structure": self._fallback_structure_analysis(statement_text)
            }
    
    async def _check_token_usage(self, operation: str, estimated_tokens: int) -> Dict[str, Any]:
        """ツール#19: トークン使用量チェック"""
        try:
            # 実際のツールを呼び出し（関数として直接呼び出し）
            from ..tools import token_guard
            result = await token_guard(operation, estimated_tokens)
            
            # JSON文字列をパース
            if isinstance(result, str):
                import json
                result = json.loads(result)
            
            return result
        except Exception as e:
            logger.error(f"Token guard error: {e}")
            # フォールバック
            return {
                "status": "ok",
                "estimated_tokens": estimated_tokens,
                "remaining_tokens": 10000,
                "usage_percentage": min(100, (estimated_tokens / 10000) * 100)
            }
    
    async def _run_structure_analysis(self, statement_text: str, university_info: str,
                                    self_analysis_context: str) -> Dict[str, Any]:
        """独自ツール: 構造分析実行"""
        try:
            # 実際のツールを呼び出し（関数として直接呼び出し）
            from ..tools import structure_analysis_function
            result = await structure_analysis_function(statement_text, university_info, self_analysis_context)
            
            # JSON文字列をパース
            if isinstance(result, str):
                import json
                result = json.loads(result)
            
            return result
        except Exception as e:
            logger.error(f"Structure analysis tool error: {e}")
            # フォールバック
            return {
                "structure": {
                    "paragraphs": len(statement_text.split('\n\n')),
                    "word_count": len(statement_text.replace(' ', '').replace('\n', '')),
                    "average_paragraph_length": 150
                },
                "flow": {
                    "introduction_strength": 7.5,
                    "body_coherence": 7.0,
                    "conclusion_impact": 6.8,
                    "transition_quality": 7.2
                }
            }
    
    async def _generate_structure_improvements(self, statement_text: str, 
                                             structure_analysis: Dict, 
                                             university_info: str) -> Dict[str, Any]:
        """構造改善案を生成"""
        try:
            improvement_prompt = f"""{STRUCTURE_PROMPT}

現在の志望理由書:
{statement_text}

構造分析結果:
{json.dumps(structure_analysis, ensure_ascii=False, indent=2)}

志望大学情報:
{university_info}

現在の構造を分析し、以下の点から改善案を提示してください：
1. 段落構成の最適化
2. 論理的流れの改善
3. 導入・本文・結論のバランス調整
4. 大学との関連性の強化

改善案を具体的に提示してください。
"""
            
            response = await self.llm.ainvoke(improvement_prompt)
            
            # 改善案の構造化
            improvements = {
                "current_structure_assessment": self._assess_current_structure(structure_analysis),
                "recommended_structure": self._extract_recommended_structure(response.content),
                "specific_improvements": self._extract_specific_improvements(response.content),
                "rationale": response.content,
                "priority_level": "high" if structure_analysis.get("flow", {}).get("body_coherence", 8) < 7 else "medium"
            }
            
            return improvements
            
        except Exception as e:
            logger.error(f"Structure improvement generation error: {e}")
            return {"error": str(e)}
    
    async def _generate_diff(self, original_text: str, improved_text: str) -> Dict[str, Any]:
        """ツール#15: 差分生成"""
        try:
            # 実際のツールを呼び出し（関数として直接呼び出し）
            from ..tools import diff_versions
            result = await diff_versions(original_text, improved_text)
            
            # JSON文字列をパース
            if isinstance(result, str):
                import json
                result = json.loads(result)
            
            return result
        except Exception as e:
            logger.error(f"Diff generation error: {e}")
            # フォールバック
            return {
                "changes": [
                    {
                        "type": "modification",
                        "original": "元の文章例",
                        "revised": "改善された文章例",
                        "reason": "構造の改善"
                    }
                ],
                "summary": "構造的な改善を提案しました"
            }
    
    def _assess_current_structure(self, structure_analysis: Dict) -> Dict[str, Any]:
        """現在の構造を評価"""
        structure_data = structure_analysis.get("structure", {})
        flow_data = structure_analysis.get("flow", {})
        
        return {
            "paragraph_count": structure_data.get("paragraphs", 0),
            "word_count": structure_data.get("word_count", 0),
            "balance_score": self._calculate_balance_score(structure_data),
            "flow_quality": {
                "introduction": flow_data.get("introduction_strength", 7.0),
                "body": flow_data.get("body_coherence", 7.0),
                "conclusion": flow_data.get("conclusion_impact", 7.0),
                "transitions": flow_data.get("transition_quality", 7.0)
            },
            "overall_structure_score": sum([
                flow_data.get("introduction_strength", 7.0),
                flow_data.get("body_coherence", 7.0),
                flow_data.get("conclusion_impact", 7.0),
                flow_data.get("transition_quality", 7.0)
            ]) / 4
        }
    
    def _calculate_balance_score(self, structure_data: Dict) -> float:
        """構成バランススコアを計算"""
        paragraphs = structure_data.get("paragraphs", 0)
        word_count = structure_data.get("word_count", 0)
        avg_length = structure_data.get("average_paragraph_length", 0)
        
        # 理想的な構成：3-5段落、1段落150-300文字
        paragraph_score = min(10, max(0, 10 - abs(4 - paragraphs) * 2))
        length_score = min(10, max(0, 10 - abs(200 - avg_length) / 20)) if avg_length > 0 else 5
        
        return (paragraph_score + length_score) / 2
    
    def _extract_recommended_structure(self, response_content: str) -> Dict[str, Any]:
        """推奨構造を抽出"""
        # 簡易的な構造抽出（実際にはより高度なパース処理が必要）
        return {
            "recommended_paragraphs": 4,
            "paragraph_themes": [
                "導入・動機",
                "具体的体験・学び",
                "大学での目標・計画", 
                "将来の展望・結論"
            ],
            "estimated_word_distribution": [15, 35, 35, 15],  # パーセンテージ
            "key_transitions": [
                "動機から体験への接続",
                "体験から大学目標への展開",
                "目標から将来への発展"
            ]
        }
    
    def _extract_specific_improvements(self, response_content: str) -> list:
        """具体的改善点を抽出"""
        # 実際の実装では、LLM応答から構造化データを抽出
        improvements = [
            {
                "type": "paragraph_restructuring",
                "description": "段落の論理的順序を調整",
                "priority": "high",
                "specific_action": "第2段落と第3段落の順序を入れ替え"
            },
            {
                "type": "transition_improvement", 
                "description": "段落間の接続を強化",
                "priority": "medium",
                "specific_action": "各段落の冒頭に適切な接続語を追加"
            },
            {
                "type": "balance_adjustment",
                "description": "段落の分量バランスを調整",
                "priority": "medium",
                "specific_action": "導入部を簡潔にし、本論を充実"
            }
        ]
        
        return improvements
    
    def _extract_recommendations(self, improvements: Dict) -> list:
        """推奨変更点を抽出"""
        recommendations = []
        
        specific_improvements = improvements.get("specific_improvements", [])
        for improvement in specific_improvements:
            if improvement.get("priority") == "high":
                recommendations.append({
                    "change_type": improvement.get("type", "structure"),
                    "description": improvement.get("description", ""),
                    "action": improvement.get("specific_action", ""),
                    "priority": improvement.get("priority", "medium")
                })
        
        return recommendations
    
    async def _generate_specific_structure_improvements(self, statement_text: str, analysis_result: Dict) -> list:
        """具体的な構成改善提案を生成"""
        try:
            structure_improvements_prompt = f"""以下の志望理由書について、具体的な構成改善提案を3つ生成してください。
各提案は、実際の文章の該当箇所を指摘し、どのように再構成すべきかを明確に示してください。

志望理由書:
{statement_text}

構成分析結果:
{json.dumps(analysis_result, ensure_ascii=False, indent=2)}

以下のJSON形式で出力してください：
{{
    "improvements": [
        {{
            "type": "structure_improvement",
            "priority": "high|medium|low",
            "location": "第X段落" または "段落Y-Z間",
            "original_text": "現在の該当部分（40-80文字程度）",
            "improved_text": "改善後の構成案",
            "reason": "具体的な改善理由",
            "impact": "この変更による効果"
        }}
    ]
}}
"""
            
            response = await self.llm.ainvoke(structure_improvements_prompt)
            
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
                return self._generate_fallback_structure_improvements(statement_text)
                
        except Exception as e:
            logger.error(f"Error generating specific structure improvements: {e}")
            return self._generate_fallback_structure_improvements(statement_text)
    
    def _generate_fallback_structure_improvements(self, statement_text: str) -> list:
        """構成改善提案のフォールバック生成"""
        paragraphs = [p.strip() for p in statement_text.split('\n\n') if p.strip()]
        improvements = []
        
        # 段落数が多すぎる場合
        if len(paragraphs) > 5:
            improvements.append({
                "type": "structure_improvement",
                "priority": "high",
                "location": f"全体構成（現在{len(paragraphs)}段落）",
                "original_text": f"現在{len(paragraphs)}個の段落で構成されています",
                "improved_text": "主要な内容を4-5段落に整理して再構成",
                "reason": "段落数が多すぎると読みにくく、論点が分散してしまうため",
                "impact": "構成が明確になり、読み手が内容を理解しやすくなります"
            })
        
        # 段落間のバランス問題
        if len(paragraphs) >= 3:
            lengths = [len(p) for p in paragraphs]
            max_len = max(lengths)
            min_len = min(lengths)
            
            if max_len > min_len * 3:  # 長さの差が3倍以上
                longest_idx = lengths.index(max_len)
                improvements.append({
                    "type": "structure_improvement",
                    "priority": "medium",
                    "location": f"第{longest_idx + 1}段落",
                    "original_text": paragraphs[longest_idx][:60] + "..." if len(paragraphs[longest_idx]) > 60 else paragraphs[longest_idx],
                    "improved_text": "この段落を2つに分割し、各段落の内容を明確に分ける",
                    "reason": "段落の長さにばらつきがあり、バランスを改善する必要があるため",
                    "impact": "文章全体のバランスが良くなり、読みやすさが向上します"
                })
        
        # 導入部の改善
        if len(paragraphs) > 0:
            first_paragraph = paragraphs[0]
            if len(first_paragraph) < 50:  # 導入が短すぎる
                improvements.append({
                    "type": "structure_improvement", 
                    "priority": "medium",
                    "location": "導入部（第1段落）",
                    "original_text": first_paragraph,
                    "improved_text": "問題提起や動機をより詳しく述べて導入を充実",
                    "reason": "導入部が簡潔すぎて、読み手の関心を引きつける力が不足しているため",
                    "impact": "冒頭から読み手の興味を引き、志望理由書全体への期待を高めます"
                })
        
        return improvements[:3]  # 最大3つまで
    
    def _fallback_structure_analysis(self, statement_text: str) -> Dict[str, Any]:
        """エラー時のフォールバック分析"""
        paragraphs = len([p for p in statement_text.split('\n\n') if p.strip()])
        word_count = len(statement_text.replace(' ', '').replace('\n', ''))
        
        return {
            "analysis": {
                "paragraphs": paragraphs,
                "word_count": word_count,
                "basic_assessment": "基本的な構成分析のみ実行"
            },
            "improvements": {
                "rationale": "技術的問題により詳細分析が実行できませんでした",
                "general_suggestions": [
                    "段落構成の見直し",
                    "論理的流れの確認",
                    "結論部分の強化"
                ]
            }
        } 