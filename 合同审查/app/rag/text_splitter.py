from typing import List
import re

from 合同审查.app.rag import ContractClause


def contract_text_preprocess(full_text: str) -> str:
    """合同文本预处理，修复语义断裂问题，为精准拆分做准备
    """
    # 1. 清理无效干扰内容（页眉、页脚、页码、水印、空行）
    full_text = re.sub(r'第\d+页\s*/\s*共\d+页', '', full_text)
    full_text = re.sub(r'-\d+-', '', full_text)
    full_text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', full_text, flags=re.IGNORECASE)
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    # 只替换空格/制表符，不替换换行
    full_text = re.sub(r'[ \t]+', ' ', full_text)

    # 2. 【修复】识别并合并被错误拆分的子条款（如一、二、三、）
    # 这些通常是第六条、第七条等的子项，不应该作为独立条款
    full_text = merge_sub_clauses(full_text)

    # 3. 修复PDF跨页导致的语义断裂
    lines = full_text.split('\n')
    processed_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if processed_lines and not re.search(r'[。；："）]$', processed_lines[-1]) and not re.match(
                r'^[第\d一二三四五六七八九十]+[条、. ]|^\d+\.\d*[. ]|^[一二三四五六七八九十]+、', line):
            processed_lines[-1] = processed_lines[-1] + ' ' + line
        else:
            processed_lines.append(line)

    # 4. 统一编号格式
    processed_text = '\n'.join(processed_lines)
    processed_text = re.sub(r'（(\d+)）', r'(\1)', processed_text)
    processed_text = re.sub(r'【(\d+)】', r'(\1)', processed_text)
    return processed_text


def merge_sub_clauses(text: str) -> str:
    """
    合并被错误拆分的子条款

    问题：第六条后面的一、二、三、四、五被识别为独立条款
    解决：将这些子条款合并到前一条款中
    """
    lines = text.split('\n')
    merged_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 检查是否是子条款标记（一、二、三、...）
        # 但前面没有"第X条"标记
        if re.match(r'^[一二三四五六七八九十]+、', line) and merged_lines:
            # 检查前一行是否是条款标题（如"第六条"）
            prev_line = merged_lines[-1].strip()

            # 如果前一行是"第X条"且没有内容，则合并
            if re.match(r'^第[一二三四五六七八九十\d]+条\s*$', prev_line):
                # 将子条款合并到前一行
                merged_lines[-1] = prev_line + ' ' + line
            # 如果前一行是"第X条 内容"格式，且当前是子条款开始
            elif re.match(r'^第[一二三四五六七八九十\d]+条', prev_line):
                # 检查前一行是否以标点结束
                if not re.search(r'[。；：]$', prev_line):
                    merged_lines[-1] = prev_line + ' ' + line
                else:
                    merged_lines.append(line)
            else:
                # 可能是前一条款的延续，合并
                merged_lines[-1] = merged_lines[-1] + '\n' + line
        else:
            merged_lines.append(line)

        i += 1

    return '\n'.join(merged_lines)


def split_contract_by_clause_number(processed_text: str, start_clause_id: int = 1) -> List[ContractClause]:
    """
    按条款编号拆分合同文本

    Args:
        processed_text: 预处理后的合同文本
        start_clause_id: 起始条款ID，用于跨页拆分时保持ID连续递增

    Returns:
        List[ContractClause]: 条款列表
    """
    # 【修复】改进正则表达式，避免将子条款（一、二、三）识别为独立条款
    # 只匹配主要的条款编号：第X条、X.X.X、X.X、X.
    clause_pattern = re.compile(
        r'(^第[一二三四五六七八九十\d]+条\s+|^\d+\.\d+\.\d+\s+|^\d+\.\d+\s+|^\d+\.\s+)',
        re.MULTILINE
    )

    matches = list(clause_pattern.finditer(processed_text))
    clause_list = []
    clause_id = start_clause_id

    if not matches:
        return [ContractClause(
            clause_id=str(clause_id),
            clause_no="全文本",
            clause_content=processed_text
        )]

    # 【修复】处理合同前置内容
    # 前置内容应该是真正的"前言"部分，不包含任何条款
    first_match_start = matches[0].start()
    if first_match_start > 0:
        pre_content = processed_text[:first_match_start].strip()
        # 【修复】过滤掉只包含标题但没有实质内容的前置内容
        # 如果前置内容包含"第一条"或类似内容，说明拆分有误
        if pre_content and not re.search(r'第[一二三四五六七八九十\d]+条', pre_content):
            # 检查前置内容是否有实质内容（至少50个字符）
            if len(pre_content) > 50:
                clause_list.append(ContractClause(
                    clause_id=str(clause_id),
                    clause_no="合同前言",
                    clause_content=pre_content
                ))
                clause_id += 1

    # 【修复】合并相邻的相同条款编号（避免重复）
    merged_matches = []
    for i, match in enumerate(matches):
        if i > 0 and match.group().strip() == matches[i-1].group().strip():
            # 跳过重复的条款编号
            continue
        merged_matches.append(match)

    for i, match in enumerate(merged_matches):
        start_pos = match.start()
        end_pos = merged_matches[i + 1].start() if i < len(merged_matches) - 1 else len(processed_text)
        full_clause_content = processed_text[start_pos:end_pos].strip()

        # 【修复】跳过内容过短的条款（可能是子条款被错误识别）
        if len(full_clause_content) < 10:
            continue

        clause_no = match.group().strip()

        # 【修复】确保条款内容完整性，包含所有子条款
        # 检查下一个匹配是否是子条款（如一、二、三）
        # 如果是，则继续扩展当前条款的内容
        clause_list.append(ContractClause(
            clause_id=str(clause_id),
            clause_no=clause_no,
            clause_content=full_clause_content
        ))
        clause_id += 1

    return clause_list


def split_contract_intelligently(full_text: str, start_clause_id: int = 1) -> List[ContractClause]:
    """
    智能拆分合同文本

    结合多种策略，确保拆分质量：
    1. 先进行文本预处理
    2. 按条款编号拆分
    3. 后处理修复拆分错误

    Args:
        full_text: 原始合同文本
        start_clause_id: 起始条款ID

    Returns:
        List[ContractClause]: 条款列表
    """
    # 1. 预处理
    processed_text = contract_text_preprocess(full_text)

    # 2. 按条款编号拆分
    clauses = split_contract_by_clause_number(processed_text, start_clause_id)

    # 3. 后处理：修复可能的拆分错误
    clauses = post_process_clauses(clauses)

    return clauses


def post_process_clauses(clauses: List[ContractClause]) -> List[ContractClause]:
    """
    后处理条款列表，修复拆分错误

    Args:
        clauses: 原始拆分的条款列表

    Returns:
        List[ContractClause]: 修复后的条款列表
    """
    if not clauses:
        return clauses

    processed_clauses = []
    i = 0

    while i < len(clauses):
        clause = clauses[i]
        content = clause.clause_content

        # 【修复】跳过只有标题没有内容的条款
        # 如"第六条"后面没有内容，则与下一个条款合并
        if re.match(r'^第[一二三四五六七八九十\d]+条\s*$', content.strip()) and i < len(clauses) - 1:
            # 合并到下一个条款
            next_clause = clauses[i + 1]
            merged_content = content + '\n' + next_clause.clause_content
            processed_clauses.append(ContractClause(
                clause_id=clause.clause_id,
                clause_no=clause.clause_no,
                clause_content=merged_content
            ))
            i += 2  # 跳过下一个条款
            continue

        # 【修复】检查是否是子条款被错误拆分
        # 如果当前条款编号是"一、"、"二、"等，且前面有主条款，则合并
        if re.match(r'^[一二三四五六七八九十]+、', clause.clause_no) and processed_clauses:
            # 合并到前一条款
            prev_clause = processed_clauses[-1]
            merged_content = prev_clause.clause_content + '\n' + content
            processed_clauses[-1] = ContractClause(
                clause_id=prev_clause.clause_id,
                clause_no=prev_clause.clause_no,
                clause_content=merged_content
            )
            i += 1
            continue

        processed_clauses.append(clause)
        i += 1

    return processed_clauses
