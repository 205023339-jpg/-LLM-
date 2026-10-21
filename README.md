# 有道翻译接口请求链路 Demo

✨ 基于 Python + PyExecJS 复现的翻译接口请求链路，
用于学习 **token 获取、参数排序、JS 签名、流式响应解析** 等前端逆向思路。


> ⚠️ 本项目仅作为个人爬虫 / 前端逆向技术学习 Demo，不包含批量采集逻辑，
> 
> 严禁用于商业用途或违规采集。所有凭证均为占位符。
> 

## 🛠 技术栈

| 类别 | 内容 |
|---|---|
| 语言 | Python 3.8+、JavaScript |
| 网络请求 | requests |
| JS 执行 | PyExecJS |
| 数据处理 | re、json |


---



## 📌 功能说明

1. **token 获取**：从独立 secret 接口获取 token（用于访问频次控制）
2. **参数拼装**：按接口声明的 `pointParam` 顺序拼接业务参数
3. **JS 签名**：调用前端 JS 函数对参数串生成 `sign`
4. **业务请求**：携带签名发起翻译请求
5. **响应解析**：从 SSE / 分段 JSON 拼接串中提取 `content` 并反转义
   ---

## 🧩 技术要点

- **token 机制**：部分接口以 token 控制访问频次，需先从独立接口获取
- **参数签名**：业务参数按接口声明顺序拼接，交由前端 JS 生成 sign
- **时间戳校验**：时间戳参与签名，须与请求体保持一致
- **签名 key**：前端 key 仅参与签名计算，不随请求体发送
- **流式解析**：返回内容为多段 JSON 拼接串，需提取 content 反转义后合并
  

> 签名算法文件源码（`js.js`）不随仓库提供，请自行用浏览器 DevTools 定位学习。
>
> 

## 📂 项目结构

.  
├── youdao_translate_demo.py # 主流程：token → 签名 → 请求 → 解析  
├── sign_demo.js # 脱敏后的签名逻辑示意（参数拼接 + MD5）  
├── README.md  
├── .gitignore  
└── screenshot/  
└── run.png # 运行效果截图
---



## 🚀 快速开始

### 安装依赖

```bash
pip install requests PyExecJS
```
