# -*- coding: utf-8 -*-
"""
有道翻译 LLM 接口请求链路 Demo（仅技术学习）

演示一条典型的前端逆向链路：
    token 获取 -> 参数排序 -> JS 签名 -> 业务请求 -> 流式响应解析

技术要点：
1. 部分接口采用 token 做访问频次控制，token 需从独立接口先行获取；
2. 业务参数按接口声明的顺序拼接后交由前端 JS 计算 sign，
   时间戳参与签名，须与请求体保持一致；前端 key 仅参与签名、不随请求发送；
3. LLM 接口返回为 SSE/分段 JSON 拼接串，需提取 content 字段并反转义后合并。

⚠️ 所有 Cookie / key / sign 均为占位符；签名 JS 不随仓库提供；
   本项目仅用于技术学习，禁止商用与违规采集。
"""

import argparse
import json
import os
import re
import time

import requests

try:
    import execjs
except ImportError:
    execjs = None


# ============================================================
#  配置区：以下字段请替换为自己抓包得到的值，切勿提交真实凭证
# ============================================================
SIGN_JS_PATH = "js.js"            # 本地签名算法文件，勿上传仓库
APP_KEY = "YOUR_APP_KEY"          # 前端硬编码 key，仅参与签名
SECRET_SIGN = "YOUR_SECRET_SIGN"  # secret 接口的 sign，抓包获取

COOKIES = {
    "OUTFOX_SEARCH_USER_ID": "YOUR_OUTFOX_SEARCH_USER_ID",
    "OUTFOX_SEARCH_USER_ID_NCOO": "YOUR_OUTFOX_SEARCH_USER_ID_NCOO",
    "DICT_DOCTRANS_SESSION_ID": "YOUR_SESSION_ID",
}

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://fanyi.youdao.com",
    "Pragma": "no-cache",
    "Referer": "https://fanyi.youdao.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

SECRET_URL = "https://luna-ai.youdao.com/translate_llm/secret"
CHAT_URL = "https://luna-ai.youdao.com/translate_llm/v3/chat"
TIMEOUT = 10

# 参与签名的参数顺序（服务端校验依据，顺序不可乱）
POINT_PARAM = (
    "appVersion,client,free,fromLang,functionEnglishName,imei,input,"
    "keyfrom,keyid,mid,model,mysticTime,network,product,roundNo,screen,"
    "showSuggest,singleBox,source,toLang,token,useTerm,vendor,yduuid,key"
)


# ============================================================
#  1. token 获取
# ============================================================
def fetch_token(yduuid: str) -> str:
    """token 用于记录访问频次，需先从独立接口获取。"""
    params = {
        "keyid": "ai-translate-llm-pre",
        "sign": SECRET_SIGN,
        "client": "fanyideskweb",
        "product": "webfanyi",
        "appVersion": "12.0.0",
        "vendor": "web",
        "pointParam": "client,mysticTime,product",
        "mysticTime": str(int(time.time() * 1000)),
        "keyfrom": "fanyi.web",
        "mid": "1",
        "screen": "1",
        "model": "1",
        "network": "wifi",
        "abtest": "0",
        "yduuid": yduuid,
    }
    resp = requests.get(
        SECRET_URL, params=params, cookies=COOKIES,
        headers=HEADERS, timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["data"]["token"]


# ============================================================
#  2. 业务参数拼装
# ============================================================
def build_payload(keyword: str, token: str, yduuid: str, timestamp: int) -> dict:
    """按接口要求组装参数；key 仅参与签名，POST 前会剔除。"""
    return {
        "product": "webfanyi",
        "appVersion": "12.0.0",
        "client": "webaitrans",
        "mid": "1",
        "vendor": "web",
        "screen": "1",
        "model": "1",
        "imei": "1",
        "network": "wifi",
        "keyfrom": "webfanyi.webaitrans",
        "keyid": "ai-translate-llm",
        "mysticTime": str(timestamp),
        "yduuid": yduuid,
        "functionEnglishName": "LLM_translate",
        "input": keyword,
        "useTerm": "0",
        "free": "false",
        "singleBox": "false",
        "fromLang": "en",
        "toLang": "zh-CHS",
        "roundNo": "1",
        "showSuggest": "0",
        "token": token,
        "source": "webaitrans",
        "pointParam": POINT_PARAM,
        "key": APP_KEY,
    }


# ============================================================
#  3. sign 生成（核心逆向点）
# ============================================================
def build_sign_string(payload: dict) -> str:
    """按 pointParam 声明顺序拼接 key=value&...，顺序错则签名失效。"""
    order = payload["pointParam"].split(",")
    return "&".join(f"{k}={payload[k]}" for k in order)


def generate_sign(js_ctx, payload: dict) -> str:
    """调用前端 JS 签名函数对拼接串做哈希。"""
    return js_ctx.call("w", build_sign_string(payload))


# ============================================================
#  4. 流式响应解析
# ============================================================
_CONTENT_RE = re.compile(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"')


def parse_stream_response(text: str) -> str:
    """
    LLM 接口常返回 SSE / 多段 JSON 拼接串，content 中可能含转义字符。
    步骤：正则提取所有 content 原文 -> 逐个 JSON 反转义 -> 拼接。
    """
    parts = _CONTENT_RE.findall(text)
    return "".join(json.loads(f'"{p}"') for p in parts)


# ============================================================
#  5. 主流程
# ============================================================
def main() -> None:
    parser = argparse.ArgumentParser(description="有道翻译接口请求链路 Demo")
    parser.add_argument("-k", "--keyword", default="hello", help="要翻译的单词")
    args = parser.parse_args()

    if execjs is None:
        raise SystemExit("缺少依赖，请先执行：pip install PyExecJS requests")
    if not os.path.exists(SIGN_JS_PATH):
        raise SystemExit(f"未找到签名算法文件 {SIGN_JS_PATH}，请自行准备（勿上传仓库）")

    with open(SIGN_JS_PATH, "r", encoding="utf-8") as f:
        js_ctx = execjs.compile(f.read())

    yduuid = js_ctx.call("C")
    token = fetch_token(yduuid)

    timestamp = int(time.time() * 1000)
    payload = build_payload(args.keyword, token, yduuid, timestamp)
    payload["sign"] = generate_sign(js_ctx, payload)
    payload.pop("key", None)  # key 仅参与签名，不发送

    resp = requests.post(
        CHAT_URL, data=payload, headers=HEADERS,
        cookies=COOKIES, timeout=TIMEOUT,
    )
    resp.raise_for_status()

    print(f"[keyword]    {args.keyword}")
    print(f"[mysticTime] {timestamp}")
    print(f"[token]      {token[:16]}...")
    print(f"[result]     {parse_stream_response(resp.text)}")


if __name__ == "__main__":
    main()