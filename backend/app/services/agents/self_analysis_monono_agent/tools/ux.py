import datetime
from io import BytesIO
from typing import List, Dict

import icalendar
from weasyprint import HTML
from PIL import Image, ImageDraw, ImageFont


def export_milestones_to_ical(milestones: List[Dict]) -> bytes:
    """milestones を iCal フォーマットのバイト列として返します"""
    cal = icalendar.Calendar()
    cal.add('prodid', '-//SelfAnalysisApp//EN')
    cal.add('version', '2.0')
    for m in milestones:
        days = m.get('days')
        kpi = m.get('kpi')
        if days is None or not isinstance(days, int):
            continue
        event = icalendar.Event()
        now = datetime.date.today()
        date = now + datetime.timedelta(days=days)
        event.add('dtstart', date)
        event.add('summary', kpi)
        event['uid'] = f"milestone-{days}-{kpi}@selfanalysis"
        cal.add_component(event)
    return cal.to_ical()


def generate_pdf_report(data: Dict) -> bytes:
    """JSON データを Markdown に変換後、1ページ PDF をバイト列で返します"""
    import markdown
    md = []
    md.append('# セッションレポート')
    # JSON を Markdown 化
    for section, content in data.get('chat', {}).items():
        md.append(f'## {section}')
        if isinstance(content, list):
            for item in content:
                md.append(f'- {item}')
        else:
            md.append(str(content))
    html = markdown.markdown('\n'.join(md))
    pdf_io = BytesIO()
    HTML(string=html).write_pdf(pdf_io)
    return pdf_io.getvalue()


def generate_summary_image(summary: str) -> bytes:
    """OpenAI Image API（gpt-image-1）でsummaryをビジュアル化し、画像バイト列を返します"""
    import os
    import requests
    import openai

    # APIキー設定
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # 画像生成リクエスト
    response = openai.Image.create(
        prompt=summary,
        n=1,
        size="1024x1024",
        model="gpt-image-1"
    )
    # 生成された画像URLを取得
    url = response["data"][0].get("url")
    if not url:
        raise RuntimeError("画像生成に失敗しました。URLが取得できませんでした。")
    # 画像データを取得
    img_resp = requests.get(url, timeout=10)
    img_resp.raise_for_status()
    return img_resp.content 