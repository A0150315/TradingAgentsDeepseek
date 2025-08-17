"""
邮件发送工具
用于发送分析结果和日志文件
"""

import os
import zipfile
import smtplib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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
        """初始化邮件发送器
        
        Args:
            smtp_server: SMTP服务器地址（可选，优先使用环境变量）
            port: SMTP端口（可选，优先使用环境变量）
            sender_email: 发送者邮箱（可选，优先使用环境变量）
            sender_name: 发送者名称（可选，优先使用环境变量）
            password: 邮箱密码或授权码（可选，优先使用环境变量）
            receiver_email: 接收者邮箱（可选，优先使用环境变量）
        """
        import os
        
        # 从环境变量读取配置，如果没有则使用传入的参数或默认值
        self.smtp_server = smtp_server or os.getenv('EMAIL_SMTP_SERVER', 'smtp.163.com')
        self.port = port or int(os.getenv('EMAIL_PORT', '25'))
        self.sender_email = sender_email or os.getenv('EMAIL_SENDER_EMAIL', 'tjqtest@163.com')
        self.sender_name = sender_name or os.getenv('EMAIL_SENDER_NAME', 'Investment')
        self.password = password or os.getenv('EMAIL_PASSWORD', '')
        self.receiver_email = receiver_email or os.getenv('EMAIL_RECEIVER_EMAIL', '')
        
        # 检查必需的配置项
        if not self.password:
            logger.warning("邮箱密码未配置，请设置EMAIL_PASSWORD环境变量")
        if not self.receiver_email:
            logger.warning("接收者邮箱未配置，请设置EMAIL_RECEIVER_EMAIL环境变量")
        
        logger.info(f"邮件发送器初始化 - SMTP: {self.smtp_server}:{self.port}, 发送者: {self.sender_name} <{self.sender_email}>")
    
    def create_analysis_package(
        self,
        csv_file: str,
        timestamp: str,
        logs_dir: str = "logs",
        output_dir: str = "packages"
    ) -> Optional[str]:
        """创建分析结果包
        
        Args:
            csv_file: CSV结果文件路径
            timestamp: 时间戳
            logs_dir: 日志目录
            output_dir: 输出目录
            
        Returns:
            打包文件路径，如果失败返回None
        """
        try:
            # 确保输出目录存在
            Path(output_dir).mkdir(exist_ok=True)
            
            # 创建压缩包文件名
            package_name = f"investment_analysis_{timestamp}.zip"
            package_path = os.path.join(output_dir, package_name)
            
            logger.info(f"开始创建分析结果包: {package_path}")
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加CSV文件
                if os.path.exists(csv_file):
                    zipf.write(csv_file, os.path.basename(csv_file))
                    logger.info(f"已添加CSV文件到压缩包: {csv_file}")
                else:
                    logger.warning(f"CSV文件不存在: {csv_file}")
                
                # 添加logs目录下的所有文件
                logs_path = Path(logs_dir)
                if logs_path.exists():
                    for file_path in logs_path.rglob('*'):
                        if file_path.is_file():
                            # 保持目录结构
                            arcname = file_path.relative_to(logs_path.parent)
                            zipf.write(file_path, arcname)
                    logger.info(f"已添加日志文件到压缩包: {logs_dir}")
                else:
                    logger.warning(f"日志目录不存在: {logs_dir}")
            
            # 检查压缩包大小
            package_size = os.path.getsize(package_path) / (1024 * 1024)  # MB
            logger.info(f"分析结果包创建完成: {package_path} ({package_size:.2f} MB)")
            
            return package_path
            
        except Exception as e:
            logger.error(f"创建分析结果包失败: {str(e)}")
            return None
    
    def send_analysis_report(
        self,
        csv_file: str,
        analysis_summary: Dict[str, Any],
        timestamp: str,
        subject_prefix: str = "投资组合分析报告"
    ) -> bool:
        """发送分析报告邮件
        
        Args:
            csv_file: CSV结果文件路径
            analysis_summary: 分析摘要信息
            timestamp: 时间戳
            subject_prefix: 邮件主题前缀
            
        Returns:
            发送是否成功
        """
        try:
            # 创建分析结果包
            package_path = self.create_analysis_package(csv_file, timestamp)
            if not package_path:
                logger.error("无法创建分析结果包，邮件发送取消")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = self.receiver_email
            msg['Subject'] = f"{subject_prefix} - {timestamp}"
            
            # 生成邮件正文
            body = self._generate_email_body(analysis_summary, timestamp)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 添加附件
            if os.path.exists(package_path):
                with open(package_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(package_path)}'
                )
                msg.attach(part)
                logger.info(f"已添加附件: {package_path}")
            
            # 发送邮件
            logger.info(f"开始发送邮件到: {self.receiver_email}")
            
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()  # 启用TLS加密
                server.login(self.sender_email, self.password)
                text = msg.as_string()
                server.sendmail(self.sender_email, self.receiver_email, text)
            
            logger.info("📧 邮件发送成功!")
            
            # 清理临时文件
            if os.path.exists(package_path):
                os.remove(package_path)
                logger.info(f"已清理临时文件: {package_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
    
    def _generate_email_body(self, summary: Dict[str, Any], timestamp: str) -> str:
        """生成邮件正文
        
        Args:
            summary: 分析摘要
            timestamp: 时间戳
            
        Returns:
            HTML格式的邮件正文
        """
        # 获取摘要信息
        total_analyzed = summary.get('total_analyzed', 0)
        successful_count = summary.get('successful_count', 0)
        failed_count = summary.get('failed_count', 0)
        execution_time = summary.get('execution_time', 0)
        
        # 获取TOP推荐（如果有结果的话）
        results = summary.get('results', [])
        top_recommendations = []
        if results:
            # 按置信度排序并取前5个
            sorted_results = sorted(results, key=lambda x: getattr(x, 'confidence_score', 0), reverse=True)
            for i, result in enumerate(sorted_results[:5], 1):
                action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(
                    getattr(result, 'recommendation', 'HOLD'), "⚪"
                )
                top_recommendations.append({
                    'rank': i,
                    'emoji': action_emoji,
                    'symbol': getattr(result, 'symbol', 'N/A'),
                    'recommendation': getattr(result, 'recommendation', 'N/A'),
                    'confidence': getattr(result, 'confidence_score', 0),
                    'target_price': getattr(result, 'target_price', 0)
                })
        
        # 生成HTML正文
        html_body = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
                .recommendations {{ margin: 20px 0; }}
                .stock-item {{ background-color: #f1f1f1; padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 投资组合分析报告</h1>
                <p>分析时间: {timestamp}</p>
            </div>
            
            <div class="content">
                <div class="summary">
                    <h2>📊 分析摘要</h2>
                    <p><strong>总股票数:</strong> {total_analyzed}</p>
                    <p><strong>成功分析:</strong> {successful_count} 支股票</p>
                    <p><strong>失败分析:</strong> {failed_count} 支股票</p>
                    <p><strong>执行时间:</strong> {execution_time:.1f} 秒</p>
                    <p><strong>成功率:</strong> {(successful_count/total_analyzed*100) if total_analyzed > 0 else 0:.1f}%</p>
                </div>
                
                {self._generate_recommendations_html(top_recommendations)}
                
                <div class="recommendations">
                    <h2>📎 附件说明</h2>
                    <p>本邮件包含以下附件:</p>
                    <ul>
                        <li><strong>CSV分析结果:</strong> 包含所有股票的详细分析数据</li>
                        <li><strong>日志文件:</strong> 完整的分析过程日志和LLM调用记录</li>
                    </ul>
                    <p>请下载附件查看完整的分析报告和日志信息。</p>
                </div>
            </div>
            
            <div class="footer">
                <p>📧 此邮件由投资组合分析系统自动发送</p>
                <p>🤖 Powered by Claude Trading Agent Framework</p>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _generate_recommendations_html(self, recommendations: List[Dict[str, Any]]) -> str:
        """生成推荐股票的HTML
        
        Args:
            recommendations: 推荐列表
            
        Returns:
            HTML字符串
        """
        if not recommendations:
            return """
            <div class="recommendations">
                <h2>🎯 分析结果</h2>
                <p>暂无成功的分析结果</p>
            </div>
            """
        
        html = """
        <div class="recommendations">
            <h2>🎯 TOP 5 推荐（按置信度排序）</h2>
            <table>
                <tr>
                    <th>排名</th>
                    <th>股票代码</th>
                    <th>推荐操作</th>
                    <th>置信度</th>
                    <th>目标价</th>
                </tr>
        """
        
        for rec in recommendations:
            html += f"""
                <tr>
                    <td>{rec['rank']}</td>
                    <td>{rec['emoji']} {rec['symbol']}</td>
                    <td>{rec['recommendation']}</td>
                    <td>{rec['confidence']:.2f}</td>
                    <td>${rec['target_price']:.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
        
        return html


def create_email_sender(**kwargs) -> EmailSender:
    """创建邮件发送器实例
    
    Args:
        **kwargs: 邮件配置参数
        
    Returns:
        EmailSender实例
    """
    return EmailSender(**kwargs)