import re
from datetime import datetime

# 匹配法规段落的正则（# 一、 # 二、 # 三、 等）
# 支持行首有空格的情况，以及标题后可能有空格或内容的情况
SECTION_SPLIT_PATTERN = re.compile(r'(?=^\s*#\s*[一二三四五六七八九十]+、)', re.MULTILINE)
LAW_NAME_PATTERN = re.compile(r'#\s*[一二三四五六七八九十]+、(.+?)(?:\s*$|\s+\n)', re.MULTILINE)

def parse_regulation(section_text):
    """解析单个法规段落的基本信息"""
    law_name_match = LAW_NAME_PATTERN.search(section_text)
    if not law_name_match:
        return None
    law_name = law_name_match.group(1).strip()

    issuer_match = re.search(r'发布机构：(.*?)(?:\r?\n|$)', section_text, re.MULTILINE)
    issuer = issuer_match.group(1).strip() if issuer_match else ""

    category_match = re.search(r'类型：(.*?)(?:\r?\n|$)', section_text, re.MULTILINE)
    category = category_match.group(1).strip() if category_match else ""

    publish_date_match = re.search(r'发布时间：(.*?)(?:\r?\n|$)', section_text, re.MULTILINE)
    publish_date = publish_date_match.group(1).strip() if publish_date_match else ""

    effective_date_match = re.search(r'生效时间：(.*?)(?:\r?\n|$)', section_text, re.MULTILINE)
    effective_date = effective_date_match.group(1).strip() if effective_date_match else ""

    description_match = re.search(r'核心应用：(.*?)(?:\r?\n|$)', section_text, re.MULTILINE)
    description = description_match.group(1).strip() if description_match else ""

    law = {
        "name": law_name,
        "category": category,
        "issuer": issuer,
        "publish_date": publish_date,
        "effective_date": effective_date,
        "status": "effective",
        "description": description,
        "is_new": 1,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return law

def parse_articles(section_text):
    """解析单个法规段落的法条列表"""
    # 匹配法条编号：支持 "1. "、"1\. "、"1 " 等多种格式
    article_blocks = re.split(r'\n\d+(?:\\?\.)?\s+', section_text)[1:]
    articles = []

    for idx, block in enumerate(article_blocks, 1):
        block = block.strip()
        if not block:
            continue

        first_line = block.split('\n')[0]
        # 匹配法条序号，如 "第一条"、"第X条" 或直接是数字
        title_match = re.match(r'^(第[一二三四五六七八九十百千]+条|\d+)\s*', first_line)
        if title_match:
            article_no = title_match.group(1)
            title = first_line[title_match.end():].strip()
        else:
            article_no = str(idx)
            title = first_line.strip()

        content_match = re.search(r'法规内容：(.*?)司法解释：', block, re.DOTALL)
        article_content = content_match.group(1).strip() if content_match else ""

        interp_match = re.search(r'司法解释：(.*?)(相关条款：|$)', block, re.DOTALL)
        interpretation = interp_match.group(1).strip() if interp_match else ""

        # 提取相关条款作为更准确的 article_no
        related_match = re.search(r'相关条款：(.*?)($|\n)', block)
        if related_match:
            related_law = related_match.group(1).strip()
            # 如果相关条款包含具体法条编号，使用它
            if related_law:
                article_no = related_law

        articles.append({
            "article_no": article_no,
            "title": title,
            "content": article_content,
            "interpretation": interpretation,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return articles

def parse_law_file(file_path):
    """
    读取法律文本文件，自动解析成数据库结构的JSON
    支持多法规段落（# 一、 # 二、 # 三、 等）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_law_content(content)

def parse_law_content(content):
    """
    解析法律文本内容，支持多法规段落
    """
    if not content or not content.strip():
        raise ValueError("法律文本内容不能为空")

    # 按法规段落分割
    sections = SECTION_SPLIT_PATTERN.split(content)
    regulations = []
    articles = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # 检查是否是法规段落（包含法规名称）
        if not LAW_NAME_PATTERN.search(section):
            continue

        # 解析法规基本信息
        regulation = parse_regulation(section)
        if not regulation:
            continue

        # 解析该法规的法条
        section_articles = parse_articles(section)

        regulations.append(regulation)
        # 为每个法条记录所属法规的索引（后续用于关联 law_id）
        for article in section_articles:
            article["_regulation_index"] = len(regulations) - 1
        articles.extend(section_articles)

    if not regulations:
        raise ValueError("未找到任何法规段落，请检查文件格式")

    result = {
        "law_regulation": regulations,
        "law_article": articles,
        "regulation_count": len(regulations),
        "article_count": len(articles)
    }
    return result

if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) > 1:
        result = parse_law_file(sys.argv[1])
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
