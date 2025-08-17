# GitHub Actions 部署指南

## 🚀 将投资组合分析器部署到GitHub Actions

### 📋 前置要求

1. **GitHub仓库**: 将代码推送到GitHub仓库
2. **API密钥**: DeepSeek API密钥
3. **邮箱配置**: 163邮箱的SMTP设置

### 🔐 配置GitHub Secrets（重要！）

在GitHub仓库中配置以下环境变量，**切勿直接写在代码中**：

#### 1. 进入仓库设置
- 打开GitHub仓库页面
- 点击 `Settings` 标签
- 在左侧菜单中找到 `Secrets and variables` → `Actions`

#### 2. 添加以下Secrets

点击 `New repository secret` 添加以下配置：

**DeepSeek API配置:**
```
名称: DEEPSEEK_API_KEY
值: xxxx

名称: DEEPSEEK_BASE_URL  
值: https://api.deepseek.com

名称: DEEPSEEK_MODEL
值: deepseek-chat
```

**邮件配置:**
```
名称: EMAIL_SMTP_SERVER
值: smtp.163.com

名称: EMAIL_PORT
值: 25

名称: EMAIL_SENDER_EMAIL
值: tjqtest@163.com

名称: EMAIL_SENDER_NAME
值: Investment

名称: EMAIL_PASSWORD
值: xxxx

名称: EMAIL_RECEIVER_EMAIL
值: 574469551@qq.com
```

### ⏰ 工作流执行时间

- **自动执行**: 每天北京时间凌晨 01:00
- **手动执行**: 在GitHub仓库的 `Actions` 标签中手动触发

### 📊 工作流功能

1. **自动安装TA-Lib**: 完整的TA-Lib C库和Python包装器安装
2. **环境配置**: 从GitHub Secrets安全读取配置
3. **分析执行**: 运行15支股票的批量分析
4. **邮件发送**: 自动发送分析报告到指定邮箱
5. **结果上传**: 将CSV和日志文件作为GitHub Artifacts保存
6. **安全清理**: 执行完成后清理敏感信息

### 🔍 监控和调试

#### 查看执行结果
1. 进入GitHub仓库的 `Actions` 标签
2. 点击对应的工作流运行记录
3. 查看各步骤的执行日志

#### 下载分析结果
1. 在工作流运行详情页面底部找到 `Artifacts`
2. 下载 `portfolio-analysis-results-xxx` 文件
3. 解压查看CSV分析结果和详细日志

#### 常见问题排查
- **API调用失败**: 检查DEEPSEEK_API_KEY是否正确
- **邮件发送失败**: 检查邮箱配置和网络连接
- **TA-Lib错误**: 查看TA-Lib安装步骤的日志

### 📧 邮件报告内容

每次分析完成后，你将收到包含以下内容的邮件：

- **HTML格式报告**: 美观的分析摘要
- **TOP 5推荐**: 按置信度排序的股票推荐
- **ZIP附件**: 包含详细的CSV数据和完整日志

### 🛡️ 安全注意事项

1. **永远不要**将API密钥和邮箱密码写在代码中
2. **使用GitHub Secrets**存储所有敏感信息
3. **定期更换**API密钥和邮箱密码
4. **检查仓库权限**，确保不会暴露Secrets

### 🎯 自定义配置

如需修改分析的股票列表或其他参数：
1. 编辑 `batch_portfolio_analyzer.py` 中的 `portfolio_symbols`
2. 推送到GitHub，下次执行时生效

### 📈 成本预估

- **GitHub Actions**: 公共仓库免费，私有仓库有免费额度
- **DeepSeek API**: 根据实际调用量计费
- **邮件发送**: 163邮箱免费

---

🎉 **部署完成后，你就拥有了一个全自动的投资组合分析系统！**