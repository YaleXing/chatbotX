# QQ 聊天机器人

一个智能 QQ 聊天机器人，支持对话、表情包、图片识别、代码回复和文件发送功能。

## ✨ 功能特点

- 🤖 **智能对话**：使用 MiMo-V2.5 全模态模型，支持自然语言对话
- 🖼️ **图片识别**：可以识别图片内容并做出有趣回复
- 🎤 **语音识别**：支持语音消息识别，自动转文字回复
- 😊 **表情包系统**：根据语境自动选择合适的表情包
- 💻 **代码处理**：识别代码、格式化、打包成文件发送
- 🔐 **权限控制**：关键指令只听从主人的命令
- 💬 **上下文记忆**：支持 100 轮对话历史
- 📢 **群聊优化**：群聊中只回复 @ 自己的消息，不乱说话

## 📋 系统要求

- Python 3.10+
- Node.js 18+（用于 NapCat）
- Windows 10/11

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 NapCat

参考 [NapCat 官方文档](https://napneko.github.io/) 安装 NapCat。

**Windows 安装方式：**

1. 下载 NapCat Shell 版本
2. 解压到任意目录
3. 运行 `napcat.bat` 登录 QQ

### 3. 配置 NapCat

登录成功后，在 NapCat WebUI（默认 http://localhost:6099）中配置：

1. 添加网络适配器
2. 选择 HTTP 服务
3. 设置端口为 3000
4. **记录 Access Token**（WebUI 会自动生成）
5. 保存配置

### 4. 配置机器人

复制 `.env.example` 为 `.env` 并填入真实配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
AI_API_KEY=your-api-key-here
AI_BASE_URL=https://api.xiaomimimo.com/v1
AI_MODEL=mimo-v2.5
QQ_API_URL=http://localhost:3000
QQ_ACCESS_TOKEN=your-access-token-here
QQ_OWNER_QQ=your-qq-number-here
```

或者复制 `config/config.example.yaml` 为 `config/config.yaml` 并编辑：

### 5. 启动机器人

```bash
python main.py
```

## 📁 项目结构

```
chatbot/
├── config/
│   ├── config.example.yaml   # 配置示例
│   └── prompts/              # 人格提示词
│       ├── default.txt       # 默认活泼可爱
│       ├── cool.txt          # 高冷话少
│       ├── funny.txt         # 搞笑幽默
│       └── gentle.txt        # 温柔体贴
├── core/
│   ├── bot.py                # 机器人主类
│   ├── ai/
│   │   ├── base.py           # AI 接口基类
│   │   └── mimo.py           # MiMo-V2.5 接入
│   ├── message/
│   │   ├── handler.py        # 消息处理器
│   │   ├── emoji.py          # 表情包管理
│   │   ├── code.py           # 代码处理
│   │   └── voice.py          # 语音处理
│   └── security/
│       └── permission.py     # 权限控制
├── platforms/
│   ├── base.py               # 平台基类
│   └── qq/
│       └── napcat.py         # NapCat 接入
├── resources/
│   └── emojis/               # 表情包库
│       ├── happy/
│       ├── sad/
│       ├── funny/
│       ├── angry/
│       ├── surprised/
│       └── love/
├── utils/
│   ├── logger.py             # 日志工具
│   └── helpers.py            # 辅助函数
├── .env.example              # 环境变量示例
├── .gitignore                # Git 忽略文件
├── main.py                   # 入口
├── requirements.txt          # 依赖
└── README.md                 # 说明文档
```

## 🎮 使用指令

### 私聊
直接发送消息即可聊天。

### 群聊
@ 机器人才会回复，不会乱说话。

| 指令 | 说明 | 权限 |
|------|------|------|
| `/帮助` | 显示帮助信息 | 所有人 |
| `/清空历史` | 清空对话历史 | 所有人 |
| `/切换人格 [名称]` | 切换机器人性格 | 主人 |
| `/查看状态` | 查看机器人状态 | 主人 |
| `/关闭机器人` | 关闭机器人 | 主人 |

## 🎭 可用人格

| 名称 | 性格 |
|------|------|
| `cute` | 活泼可爱（默认） |
| `cool` | 高冷话少 |
| `funny` | 搞笑幽默 |
| `gentle` | 温柔体贴 |

切换人格示例：
```
/切换人格 cool
```

## 😊 表情包系统

机器人会根据对话内容自动选择合适的表情包。

表情包存放在 `resources/emojis/` 目录下：
- `happy/` - 开心的表情
- `sad/` - 难过的表情
- `funny/` - 搞笑的表情
- `angry/` - 生气的表情
- `surprised/` - 惊讶的表情
- `love/` - 爱心的表情

你可以自己添加表情包到对应目录。

## 🔐 安全说明

- 关键指令只响应主人的 QQ 号
- 不执行任何系统命令
- 不访问电脑文件系统
- 所有操作都有日志记录

## 🛠️ 故障排除

### NapCat 连接失败

1. 确保 NapCat 已启动并登录成功
2. 检查 NapCat WebUI 中的 HTTP 服务配置
3. 确认端口 3000 未被占用

### AI 回复失败

1. 检查 API Key 是否正确
2. 确认网络可以访问 api.siliconflow.cn
3. 查看日志文件中的错误信息

### 表情包不发送

1. 确认 `resources/emojis/` 目录下有表情包文件
2. 检查 `config.yaml` 中的 `emoji.enabled` 是否为 `true`
3. 调整 `emoji.probacity` 参数

## 📝 更新日志

### v1.0.0 (2026-06-17)
- 初始版本发布
- 支持基本对话功能
- 支持图片识别
- 支持语音识别
- 支持表情包系统
- 支持代码打包发送

## 📄 许可证

MIT License

## 🙏 致谢

- [NapCat](https://github.com/NapNeko/NapCatQQ) - QQ 协议实现
- [小米 MiMo](https://api.xiaomimimo.com) - AI 模型 API
- [OneBot](https://11.onebot.dev/) - 机器人协议标准
