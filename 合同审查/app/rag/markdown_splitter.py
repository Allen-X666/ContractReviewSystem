"""
Markdown 文档拆分器

支持按标题层级拆分 Markdown 文档，
可配置拆分深度和最小内容长度。
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MarkdownSection:
    """Markdown 文档章节"""
    id: str
    level: int  # 标题级别 (1-6)
    title: str
    content: str  # 包含标题和正文
    heading: str  # 原始标题行
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarkdownSplitter:
    """
    Markdown 文档拆分器

    按标题层级拆分文档，支持配置：
    - 最大拆分深度（如只拆分到 ### 级别）
    - 最小内容长度（过滤过短的段落）
    """

    def __init__(
        self,
        max_depth: int = 3,  # 最大拆分深度，默认拆分到 ###
        min_content_length: int = 50,  # 最小内容长度
        preserve_hierarchy: bool = True,  # 是否保留层级信息
    ):
        self.max_depth = max_depth
        self.min_content_length = min_content_length
        self.preserve_hierarchy = preserve_hierarchy

    def split(self, content: str) -> List[MarkdownSection]:
        """
        拆分 Markdown 文档

        按标题层级拆分文档，每个章节包含该标题及其下的所有内容，
        直到下一个同等级或更高等级的标题。

        Args:
            content: Markdown 文本内容

        Returns:
            List[MarkdownSection]: 拆分后的章节列表
        """
        lines = content.split('\n')

        # 首先找出所有标题及其位置
        headings = []
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append({
                    'index': i,
                    'level': level,
                    'title': title,
                    'line': line,
                })

        if not headings:
            # 没有标题，整个文档作为一个章节
            if content.strip():
                return [MarkdownSection(
                    id="1",
                    level=0,
                    title="完整文档",
                    content=content.strip(),
                    heading="",
                )]
            return []

        # 根据标题拆分章节
        sections = []
        for i, heading in enumerate(headings):
            # 只处理指定深度以内的标题
            if heading['level'] > self.max_depth:
                continue

            # 确定当前章节的结束位置
            start_idx = heading['index']
            if i + 1 < len(headings):
                # 找到下一个同等级或更高等级的标题
                end_idx = len(lines)
                for next_heading in headings[i + 1:]:
                    if next_heading['level'] <= heading['level']:
                        end_idx = next_heading['index']
                        break
            else:
                end_idx = len(lines)

            # 提取章节内容
            section_lines = lines[start_idx:end_idx]
            section_content = '\n'.join(section_lines).strip()

            # 检查内容长度
            if len(section_content) >= self.min_content_length:
                sections.append(MarkdownSection(
                    id=str(len(sections) + 1),
                    level=heading['level'],
                    title=heading['title'],
                    content=section_content,
                    heading=heading['line'],
                ))

        # 如果没有拆分到任何章节（可能都太短），将整个文档作为一个章节
        if not sections and content.strip():
            sections.append(MarkdownSection(
                id="1",
                level=0,
                title="完整文档",
                content=content.strip(),
                heading="",
            ))

        return sections

    def split_with_context(self, content: str) -> List[MarkdownSection]:
        """
        拆分并添加上下文信息

        为每个章节添加父级标题信息，便于理解上下文。

        Args:
            content: Markdown 文本内容

        Returns:
            List[MarkdownSection]: 带上下文的章节列表
        """
        sections = self.split(content)

        if not self.preserve_hierarchy or len(sections) <= 1:
            return sections

        # 构建层级路径
        hierarchy_stack = []

        for section in sections:
            # 弹出比当前级别高或同级的标题
            while hierarchy_stack and hierarchy_stack[-1][0] >= section.level:
                hierarchy_stack.pop()

            # 构建完整路径
            if hierarchy_stack:
                parent_path = ' > '.join([h[1] for h in hierarchy_stack])
                section.metadata['parent_path'] = parent_path
                section.metadata['full_title'] = f"{parent_path} > {section.title}"
            else:
                section.metadata['full_title'] = section.title

            # 将当前标题压入栈
            hierarchy_stack.append((section.level, section.title))

        return sections


def split_markdown(
    content: str,
    max_depth: int = 3,
    min_content_length: int = 50,
) -> List[MarkdownSection]:
    """
    便捷函数：拆分 Markdown 文档

    Args:
        content: Markdown 文本内容
        max_depth: 最大拆分深度
        min_content_length: 最小内容长度

    Returns:
        List[MarkdownSection]: 拆分后的章节列表
    """
    splitter = MarkdownSplitter(
        max_depth=max_depth,
        min_content_length=min_content_length,
    )
    return splitter.split(content)


if __name__ == "__main__":
    # 测试 Markdown 拆分器
    test_content = """# 合同审查系统 - 用户操作手册

## 1. 快速开始

### 1.1 如何登录系统？

1. 打开浏览器，访问系统地址
2. 在登录页面选择登录方式
3. 点击"登录"按钮

### 1.2 如何注册账号？

1. 在登录页面点击"立即注册"
2. 填写注册信息
3. 点击"注册"按钮

## 2. 合同管理

### 2.1 如何上传合同文件？

支持两种方式上传合同文件...

### 2.2 如何查看合同列表？

点击左侧菜单"合同列表"...

## 3. 常见问题

Q1: 支持哪些文件格式？
A: 目前支持 PDF 和 DOCX 格式。
"""

    splitter = MarkdownSplitter(max_depth=3)
    sections = splitter.split_with_context(test_content)

    print(f"共拆分成 {len(sections)} 个章节:\n")

    for section in sections:
        print(f"ID: {section.id}")
        print(f"级别: {'#' * section.level if section.level > 0 else '正文'}")
        print(f"标题: {section.title}")
        if 'full_title' in section.metadata:
            print(f"完整路径: {section.metadata['full_title']}")
        print(f"内容长度: {len(section.content)} 字符")
        print(f"内容预览: {section.content[:100]}...")
        print("-" * 50)
