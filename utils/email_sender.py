"""邮件发送工具"""

import os
import smtplib
from typing import Optional, Dict, Any, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils.logger import get_logger

logger = get_logger()


class EmailSender:
    """邮件发送器"""
    
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        port: Optional[int] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        password: Optional[str] = None,
        receiver_email: Optional[str] = None
    ):
        self.smtp_server = smtp_server or os.getenv('EMAIL_SMTP_SERVER', 'smtp.163.com')
        self.port = port or int(os.getenv('EMAIL_PORT', '25'))
        self.sender_email = sender_email or os.getenv('EMAIL_SENDER_EMAIL', 'tjqtest@163.com')
        self.sender_name = sender_name or os.getenv('EMAIL_SENDER_NAME', 'Investment')
        self.password = password or os.getenv('EMAIL_PASSWORD', '')
        self.receiver_email = receiver_email or os.getenv('EMAIL_RECEIVER_EMAIL', '')
        
        if not self.password:
            logger.warning("邮箱密码未配置，请设置EMAIL_PASSWORD环境变量")
        if not self.receiver_email:
            logger.warning("接收者邮箱未配置，请设置EMAIL_RECEIVER_EMAIL环境变量")
        
        logger.info(f"邮件发送器初始化 - SMTP: {self.smtp_server}:{self.port}")
    
    def send_analysis_report(
        self,
        csv_file: str,
        analysis_summary: Dict[str, Any],
        timestamp: str,
        subject_prefix: str = "投资组合分析报告"
    ) -> bool:
        """发送分析报告邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = self.receiver_email
            msg['Subject'] = f"{subject_prefix} - {timestamp}"
            
            body = self._generate_email_body(analysis_summary, timestamp)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            logger.info(f"开始发送邮件到: {self.receiver_email}")
            
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            
            logger.info("📧 邮件发送成功!")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
    
    def _generate_email_body(self, summary: Dict[str, Any], timestamp: str) -> str:
        """生成邮件HTML正文"""
        total_analyzed = summary.get('total_analyzed', 0)
        successful_count = summary.get('successful_count', 0)
        failed_count = summary.get('failed_count', 0)
        execution_time = summary.get('execution_time', 0)
        results = summary.get('results', [])
        success_rate = (successful_count / total_analyzed * 100) if total_analyzed > 0 else 0
        

        return f"""
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
        .recommendations, .budget-section {{ margin: 30px 0; }}
        .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; background-color: #4CAF50; color: white; font-size: 12px; margin-left: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 投资组合分析报告</h1>
        <p>{timestamp}</p>
    </div>
    
    <div class="content">
        <div class="summary">
            <h2>📊 分析摘要</h2>
            <p><strong>总股票数:</strong> {total_analyzed} | <strong>成功:</strong> {successful_count} | <strong>失败:</strong> {failed_count}</p>
            <p><strong>执行时间:</strong> {execution_time:.1f}秒 | <strong>成功率:</strong> {success_rate:.1f}%</p>
        </div>
        
        {self._generate_recommendations_html(results)}
        {self._generate_budget_sections(results)}
    </div>
    
    <div class="footer">
        <p>📧 投资组合分析系统自动发送 | 🤖 Powered by Claude Trading Agent Framework</p>
    </div>
</body>
</html>
"""
    
    def _generate_recommendations_html(self, results: List[Any]) -> str:
        """生成TOP推荐概览"""
        if not results:
            return '<div class="recommendations"><h2>🎯 分析结果</h2><p>暂无成功的分析结果</p></div>'

        sorted_results = sorted(results, key=lambda x: self._get_value(x, 'confidence_score', 0) or 0, reverse=True)
        emoji_map = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
        
        rows = []
        for idx, result in enumerate(sorted_results[:5], 1):
            rec = self._get_value(result, 'recommendation', 'N/A')
            conf = self._get_value(result, 'confidence_score', 0) or 0
            target = self._get_value(result, 'target_price')
            symbol = self._get_value(result, 'symbol', 'N/A')
            emoji = emoji_map.get(rec, "⚪")
            
            rows.append(f'<tr><td>{idx}</td><td>{emoji} {symbol}</td><td>{rec}</td><td>{conf:.2f}</td><td>{self._fmt_currency(target)}</td></tr>')

        return f'''
<div class="recommendations">
    <h2>🎯 TOP 5 推荐（按置信度排序）</h2>
    <table>
        <tr><th>排名</th><th>股票代码</th><th>推荐操作</th><th>置信度</th><th>目标价</th></tr>
        {''.join(rows)}
    </table>
</div>
'''

    def _generate_budget_sections(self, results: List[Any]) -> str:
        """生成不同预算下的资金分配表格"""
        if not results:
            return '<div class="budget-section"><h2>💰 预算方案</h2><p>暂无可用的交易建议数据</p></div>'

        sections = []
        emoji_map = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
        for budget in [1000, 2000, 1500]:
            rows = []
            for result in results:
                symbol = self._get_value(result, 'symbol', 'N/A')
                recommendation = self._get_value(result, 'recommendation', 'N/A')
                recommendation_display = f"{emoji_map.get(recommendation, '⚪')} {recommendation}"
                pos_size = self._get_value(result, 'position_size', 0) or 0
                max_price = self._get_value(result, 'acceptable_price_max')
                stop_loss = self._get_value(result, 'stop_loss')
                take_profit = self._get_value(result, 'take_profit')
                allocation = budget * pos_size if pos_size else 0
                
                rows.append(
                    f'<tr>'
                    f'<td>{symbol}</td>'
                    f'<td>{recommendation_display}</td>'
                    f'<td>{self._fmt_currency(budget)}</td>'
                    f'<td>{self._fmt_percentage(pos_size)}</td>'
                    f'<td>{self._fmt_currency(allocation)}</td>'
                    f'<td>{self._fmt_currency(max_price)}</td>'
                    f'<td>{self._fmt_currency(stop_loss)}</td>'
                    f'<td>{self._fmt_currency(take_profit)}</td>'
                    f'</tr>'
                )
            
            sections.append(f'''
<div class="budget-section">
    <h2>💰 预算方案：每只股票 {self._fmt_currency(budget)}<span class="badge">固定预算</span></h2>
    <table>
        <tr><th>股票代码</th><th>建议方向</th><th>预算金额</th><th>建议仓位</th><th>建议投入金额</th><th>可接受最高价</th><th>止损价</th><th>止盈价</th></tr>
        {''.join(rows)}
    </table>
</div>
''')
        
        return ''.join(sections)

    def _get_value(self, result: Any, attr: str, default: Any = None) -> Any:
        """从结果对象或字典中获取属性值"""
        if hasattr(result, attr):
            value = getattr(result, attr)
            return default if value is None else value
        if isinstance(result, dict):
            return result.get(attr, default)
        return default

    def _fmt_currency(self, value: Optional[float]) -> str:
        """格式化货币"""
        if value is None:
            return "N/A"
        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    def _fmt_percentage(self, value: Optional[float]) -> str:
        """格式化百分比"""
        if value is None:
            return "0.0%"
        try:
            return f"{float(value) * 100:.1f}%"
        except (TypeError, ValueError):
            return str(value)


def create_email_sender(**kwargs) -> EmailSender:
    """创建邮件发送器实例"""
    return EmailSender(**kwargs)