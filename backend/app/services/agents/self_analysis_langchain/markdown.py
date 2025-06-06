def render_markdown_timeline(timeline: list[dict]) -> str:
    """
    タイムラインのリストを受け取り、Markdownの表形式に変換して返します。
    """
    header = "| 年 | 出来事 | 詳細 | スキル | 価値観 |\n| --- | --- | --- | --- | --- |\n"
    rows = []
    for item in timeline:
        year = item.get("year", "")
        event = item.get("event", "")
        detail = item.get("detail", "")
        skills = ", ".join(item.get("skills", []))
        values = ", ".join(item.get("values", []))
        rows.append(f"| {year} | {event} | {detail} | {skills} | {values} |")
    return header + "\n".join(rows) 