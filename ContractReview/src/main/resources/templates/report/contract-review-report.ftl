<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>合同审查报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #1f2937;
            background: #ffffff;
        }

        .report-wrapper {
            width: 100%;
            background: #ffffff;
        }

        .report-header-bar {
            height: 3px;
            background: #1a2744;
        }

        /* ==================== 封面样式 ==================== */
        .report-cover {
            padding: 80px 60px;
            text-align: center;
            border-bottom: 3px solid #1a2744;
        }

        .cover-header {
            margin-bottom: 60px;
        }

        .company-logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 24px;
            background: #1a2744;
            border-radius: 50%;
            text-align: center;
            line-height: 80px;
            color: #ffffff;
            font-size: 36px;
            font-weight: bold;
        }

        .cover-title {
            font-size: 36px;
            font-weight: 700;
            color: #1a2744;
            margin: 0 0 8px 0;
            letter-spacing: 4px;
        }

        .cover-subtitle {
            font-size: 14px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .cover-info {
            width: 400px;
            margin: 0 auto 60px;
            text-align: left;
        }

        .info-row {
            padding: 12px 0;
            border-bottom: 1px solid #e5e7eb;
        }

        .info-label {
            width: 100px;
            display: inline-block;
            color: #6b7280;
            font-size: 14px;
        }

        .info-value {
            color: #1f2937;
            font-weight: 500;
        }

        .cover-score {
            text-align: center;
        }

        .score-circle {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            margin: 0 auto 16px;
            text-align: center;
            padding-top: 30px;
        }

        .score-circle.excellent {
            background: #059669;
        }

        .score-circle.good {
            background: #d97706;
        }

        .score-circle.poor {
            background: #dc2626;
        }

        .score-value {
            font-size: 36px;
            font-weight: 700;
            color: #ffffff;
            line-height: 1;
        }

        .score-label {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.9);
            margin-top: 4px;
        }

        .score-assessment {
            font-size: 18px;
            font-weight: 600;
        }

        .score-assessment.excellent { color: #059669; }
        .score-assessment.good { color: #d97706; }
        .score-assessment.poor { color: #dc2626; }

        /* ==================== 章节样式 ==================== */
        .report-section {
            padding: 40px 60px;
            border-bottom: 1px solid #e5e7eb;
        }

        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #1a2744;
            margin: 0 0 24px 0;
            padding-bottom: 12px;
            border-bottom: 2px solid #1a2744;
        }

        .section-number {
            display: inline-block;
            width: 32px;
            height: 32px;
            background: #1a2744;
            color: #ffffff;
            border-radius: 50%;
            text-align: center;
            line-height: 32px;
            font-size: 16px;
            margin-right: 12px;
            vertical-align: middle;
        }

        .section-title-text {
            vertical-align: middle;
        }

        /* ==================== 统计卡片 ==================== */
        .overview-stats {
            width: 100%;
            margin-bottom: 32px;
        }

        .overview-stats table {
            width: 100%;
            border-collapse: collapse;
        }

        .overview-stats td {
            width: 25%;
            text-align: center;
            padding: 20px 12px;
            border: 1px solid #e5e7eb;
            vertical-align: top;
        }

        .stat-icon {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            margin: 0 auto 10px;
            text-align: center;
            line-height: 42px;
            font-size: 18px;
        }

        .stat-icon.high { background: #fef2f2; color: #dc2626; }
        .stat-icon.medium { background: #fffbeb; color: #f59e0b; }
        .stat-icon.low { background: #eff6ff; color: #2563eb; }
        .stat-icon.none { background: #ecfdf5; color: #10b981; }

        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #111827;
            line-height: 1;
        }

        .stat-label {
            font-size: 12px;
            color: #6b7280;
            margin-top: 4px;
            letter-spacing: 1px;
        }

        /* ==================== 饼图 ==================== */
        .overview-chart {
            text-align: center;
            margin-bottom: 32px;
        }

        .chart-container {
            display: inline-block;
        }

        .chart-pie-container {
            display: inline-block;
            vertical-align: middle;
        }

        .chart-legend {
            display: inline-block;
            vertical-align: middle;
            margin-left: 48px;
            text-align: left;
        }

        .chart-legend-item {
            margin-bottom: 14px;
        }

        .chart-legend-dot {
            display: inline-block;
            width: 14px;
            height: 14px;
            border-radius: 4px;
            vertical-align: middle;
            margin-right: 12px;
        }

        .chart-legend-dot.high { background: #dc2626; }
        .chart-legend-dot.medium { background: #d97706; }
        .chart-legend-dot.low { background: #2563eb; }
        .chart-legend-dot.none { background: #10b981; }

        .chart-legend-name {
            font-size: 13px;
            color: #4b5563;
            font-weight: 500;
        }

        .chart-legend-count {
            font-size: 20px;
            font-weight: 700;
            color: #111827;
        }

        .chart-legend-percent {
            font-size: 11px;
            color: #9ca3af;
        }

        /* ==================== 审查结论 ==================== */
        .overview-summary {
            background: #f9fafb;
            border-radius: 16px;
            padding: 24px 28px;
            border: 1px solid #e5e7eb;
            border-left: 4px solid #c9a84c;
        }

        .overview-summary h4 {
            font-size: 15px;
            color: #111827;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }

        .overview-summary p {
            color: #4b5563;
            line-height: 1.8;
            font-size: 14px;
        }

        /* ==================== 风险卡片 ==================== */
        .risks-content {
            width: 100%;
        }

        .risk-detail-item {
            margin-bottom: 20px;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            overflow: hidden;
        }

        .risk-detail-item.risk-high { border-left: 5px solid #dc2626; }
        .risk-detail-item.risk-medium { border-left: 5px solid #f59e0b; }
        .risk-detail-item.risk-low { border-left: 5px solid #2563eb; }

        .risk-header {
            padding: 16px 20px;
            background: #f9fafb;
            border-bottom: 1px solid #f3f4f6;
        }

        .risk-number {
            display: inline-block;
            width: 30px;
            height: 30px;
            background: #1f2937;
            color: #ffffff;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            font-weight: 700;
            font-size: 13px;
            margin-right: 12px;
            vertical-align: middle;
        }

        .risk-tag {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #ffffff;
            margin-right: 12px;
            vertical-align: middle;
        }

        .risk-tag.high { background: #dc2626; }
        .risk-tag.medium { background: #f59e0b; color: #7c2d12; }
        .risk-tag.low { background: #2563eb; }

        .risk-clause {
            font-weight: 600;
            color: #1f2937;
            font-size: 14px;
            vertical-align: middle;
        }

        .risk-body {
            padding: 20px;
        }

        .risk-section {
            margin-bottom: 16px;
        }

        .risk-section:last-child {
            margin-bottom: 0;
        }

        .risk-section h5 {
            font-size: 11px;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 6px;
        }

        .risk-section p {
            color: #4b5563;
            line-height: 1.7;
            font-size: 13px;
        }

        .clause-text {
            background: #f9fafb;
            padding: 14px 18px;
            border-radius: 6px;
            font-style: italic;
            color: #6b7280;
            border: 1px solid #e5e7eb;
            font-size: 13px;
            line-height: 1.7;
        }

        .law-list {
            width: 100%;
        }

        .law-reference {
            background: #ffffff;
            padding: 12px 16px;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
            margin-bottom: 8px;
        }

        .law-content {
            color: #4b5563;
            font-size: 12px;
            line-height: 1.6;
        }

        .law-interpretation {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px dashed #e5e7eb;
            color: #6b7280;
            font-size: 12px;
        }

        .suggestion-box {
            background: #f0fdf6;
            padding: 16px 18px;
            border-radius: 6px;
            border-left: 3px solid #10b981;
            color: #374151;
            font-size: 13px;
            line-height: 1.7;
        }

        /* ==================== 表格 ==================== */
        .suggestions-summary {
            width: 100%;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
        }

        table.suggestions-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        table.suggestions-table thead th {
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
            padding: 14px 16px;
            text-align: left;
            border-bottom: 2px solid #e5e7eb;
            font-size: 12px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        table.suggestions-table tbody td {
            padding: 12px 16px;
            border-bottom: 1px solid #f3f4f6;
            color: #4b5563;
            vertical-align: top;
        }

        table.suggestions-table tbody tr:last-child td {
            border-bottom: none;
        }

        .suggestion-cell {
            max-width: 320px;
            line-height: 1.6;
        }

        /* ==================== 页脚 ==================== */
        .report-footer {
            text-align: center;
            padding: 28px 48px;
            background: #ffffff;
            border-top: 1px solid #e5e7eb;
            color: #9ca3af;
            font-size: 11px;
            letter-spacing: 1px;
            line-height: 1.8;
        }

        @page {
            size: A4;
            margin: 12mm;
        }

        @media print {
            body { background: white; }
            .report-wrapper { width: 100%; margin: 0; }
            .report-section { page-break-inside: avoid; }
            .risk-detail-item { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
<div class="report-wrapper">
    <div class="report-header-bar"></div>

    <!-- 报告封面 -->
    <div class="report-cover">
        <div class="cover-header">
            <div class="company-logo">合</div>
            <h1 class="cover-title">${title!"合同审查报告"}</h1>
            <div class="cover-subtitle">Contract Review Report</div>
        </div>

        <div class="cover-info">
            <div class="info-row">
                <span class="info-label">合同名称</span>
                <span class="info-value">${contractName!"未命名合同"}</span>
            </div>
            <div class="info-row">
                <span class="info-label">审查编号</span>
                <span class="info-value">${reviewId!"—"}</span>
            </div>
            <div class="info-row">
                <span class="info-label">审查时间</span>
                <span class="info-value">${completedAt!"—"}</span>
            </div>
            <div class="info-row">
                <span class="info-label">审查机构</span>
                <span class="info-value">${reviewAgency!"智能合同审查系统"}</span>
            </div>
        </div>

        <div class="cover-score">
            <div class="score-circle ${assessmentClass!"poor"}">
                <div class="score-value">${overallScore!0}</div>
                <div class="score-label">综合评分</div>
            </div>
            <div class="score-assessment ${assessmentClass!"poor"}">${assessmentText!"需改进"}</div>
        </div>
    </div>

    <!-- 审查概览 -->
    <div class="report-section">
        <h2 class="section-title">
            <span class="section-number">一</span>
            <span class="section-title-text">审查概览</span>
        </h2>

        <div class="overview-stats">
            <table>
                <tr>
                    <td>
                        <div class="stat-icon high">高</div>
                        <div class="stat-value">${highRiskCount!0}</div>
                        <div class="stat-label">高风险</div>
                    </td>
                    <td>
                        <div class="stat-icon medium">中</div>
                        <div class="stat-value">${mediumRiskCount!0}</div>
                        <div class="stat-label">中风险</div>
                    </td>
                    <td>
                        <div class="stat-icon low">低</div>
                        <div class="stat-value">${lowRiskCount!0}</div>
                        <div class="stat-label">低风险</div>
                    </td>
                    <td>
                        <div class="stat-icon none">无</div>
                        <div class="stat-value">${noRiskCount!0}</div>
                        <div class="stat-label">无风险</div>
                    </td>
                </tr>
            </table>
        </div>

        <div class="overview-chart">
            <div class="chart-container">
                <div class="chart-pie-container">
                    <svg viewBox="0 0 200 200" width="180" height="180">
                        <circle cx="100" cy="100" r="85" fill="#f3f4f6" stroke="#fff" stroke-width="4"/>
                        <#if totalRisks?? && totalRisks gt 0>
                            <#if (highRiskCount!0) gt 0>
                                <path d="M100,100 L100,15 A85,85 0 ${highLargeArc!0},1 ${highEndX!100},${highEndY!100}" fill="#dc2626" stroke="#fff" stroke-width="2"/>
                            </#if>
                            <#if (mediumRiskCount!0) gt 0>
                                <path d="M100,100 L${mediumStartX!100},${mediumStartY!100} A85,85 0 ${mediumLargeArc!0},1 ${mediumEndX!100},${mediumEndY!100}" fill="#f59e0b" stroke="#fff" stroke-width="2"/>
                            </#if>
                            <#if (lowRiskCount!0) gt 0>
                                <path d="M100,100 L${lowStartX!100},${lowStartY!100} A85,85 0 ${lowLargeArc!0},1 ${lowEndX!100},${lowEndY!100}" fill="#2563eb" stroke="#fff" stroke-width="2"/>
                            </#if>
                            <#if (noRiskCount!0) gt 0>
                                <path d="M100,100 L${noStartX!100},${noStartY!100} A85,85 0 ${noLargeArc!0},1 100,15" fill="#10b981" stroke="#fff" stroke-width="2"/>
                            </#if>
                            <circle cx="100" cy="100" r="40" fill="#fff"/>
                        <#else>
                            <circle cx="100" cy="100" r="40" fill="#fff"/>
                        </#if>
                    </svg>
                </div>
                <div class="chart-legend">
                    <div class="chart-legend-item">
                        <span class="chart-legend-dot high"></span>
                        <span class="chart-legend-name">高风险</span>
                        <span class="chart-legend-count">${highRiskCount!0}</span>
                        <span class="chart-legend-percent">(${highRiskPercent!0}%)</span>
                    </div>
                    <div class="chart-legend-item">
                        <span class="chart-legend-dot medium"></span>
                        <span class="chart-legend-name">中风险</span>
                        <span class="chart-legend-count">${mediumRiskCount!0}</span>
                        <span class="chart-legend-percent">(${mediumRiskPercent!0}%)</span>
                    </div>
                    <div class="chart-legend-item">
                        <span class="chart-legend-dot low"></span>
                        <span class="chart-legend-name">低风险</span>
                        <span class="chart-legend-count">${lowRiskCount!0}</span>
                        <span class="chart-legend-percent">(${lowRiskPercent!0}%)</span>
                    </div>
                    <div class="chart-legend-item">
                        <span class="chart-legend-dot none"></span>
                        <span class="chart-legend-name">无风险</span>
                        <span class="chart-legend-count">${noRiskCount!0}</span>
                        <span class="chart-legend-percent">(${noRiskPercent!0}%)</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="overview-summary">
            <h4>审查结论</h4>
            <p>${conclusion!"经系统审查，本合同存在若干需要关注的风险点，建议根据修改建议进行调整后再签署。"}</p>
        </div>
    </div>

    <!-- 风险详情 -->
    <div class="report-section">
        <h2 class="section-title">
            <span class="section-number">二</span>
            <span class="section-title-text">风险详情</span>
        </h2>

        <div class="risks-content">
            <#if risks?? && risks?has_content>
                <#list risks as risk>
                    <div class="risk-detail-item risk-${risk.level}">
                        <div class="risk-header">
                            <span class="risk-number">${risk?index + 1}</span>
                            <span class="risk-tag ${risk.level}">${risk.levelText!"高风险"}</span>
<#--                            <span class="risk-clause">${risk.clause!"未知条款"}</span>-->
                        </div>

                        <div class="risk-body">
                            <div class="risk-section">
                                <h5>涉及条款</h5>
                                <p class="clause-text">${risk.locationText!"合同相关条款"}</p>
                            </div>

                            <div class="risk-section">
                                <h5>问题描述</h5>
                                <p>${risk.description!"暂无描述"}</p>
                            </div>

                            <#if risk.lawReferences?? && risk.lawReferences?has_content>
                                <div class="risk-section">
                                    <h5>法律依据</h5>
                                    <div class="law-list">
                                        <#list risk.lawReferences as law>
                                            <div class="law-reference">
                                                <div class="law-content">${law.content!"暂无内容"}</div>
                                                <#if law.interpretation?? && law.interpretation != "">
                                                    <div class="law-interpretation">
                                                        <strong>司法解释：</strong>${law.interpretation}
                                                    </div>
                                                </#if>
                                            </div>
                                        </#list>
                                    </div>
                                </div>
                            </#if>

                            <div class="risk-section suggestion">
                                <h5>修改建议</h5>
                                <div class="suggestion-box">
                                    <p>${risk.suggestion!"暂无建议"}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </#list>
            <#else>
                <p style="text-align: center; color: #6b7280; padding: 40px 0;">暂无风险项</p>
            </#if>
        </div>
    </div>

    <!-- 修改建议汇总 -->
    <div class="report-section">
        <h2 class="section-title">
            <span class="section-number">三</span>
            <span class="section-title-text">修改建议汇总</span>
        </h2>

        <div class="suggestions-summary">
            <table class="suggestions-table">
                <thead>
                    <tr>
                        <th style="width: 60px">序号</th>
                        <th style="width: 100px">风险等级</th>
                        <th style="width: 150px">涉及条款</th>
                        <th>修改建议</th>
                        <th style="width: 80px">优先级</th>
                    </tr>
                </thead>
                <tbody>
                    <#if sortedRisks?? && sortedRisks?has_content>
                        <#list sortedRisks as risk>
                            <tr>
                                <td>${risk?index + 1}</td>
                                <td>
                                    <span class="risk-tag ${risk.level}">${risk.levelText!"高风险"}</span>
                                </td>
                                <td>${risk.locationText!risk.clause!"未知条款"}</td>
                                <td class="suggestion-cell">${risk.suggestion!"暂无建议"}</td>
                                <td>${risk.priorityText!"高"}</td>
                            </tr>
                        </#list>
                    <#else>
                        <tr>
                            <td colspan="5" style="text-align: center; color: #6b7280; padding: 20px 0;">暂无风险项</td>
                        </tr>
                    </#if>
                </tbody>
            </table>
        </div>
    </div>

    <!-- 报告页脚 -->
    <div class="report-footer">
        <p>本报告由智能合同审查系统自动生成，仅供参考</p>
        <p>报告生成时间：${generatedAt!"—"}</p>
    </div>
</div>
</body>
</html>
