"""
本地测试服务器 — 为 localhost/ 前端提供 API
启动: python localhost_server.py
访问: http://localhost:8899
"""
import os
import sys
import json
import io

# 确保能导入同目录的 agent_core 和 tools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory

from agent_core import run_agent
from tools import parse_file_content, set_uploaded_file, get_uploaded_file_info

app = Flask(__name__, static_folder="localhost", static_url_path="")


@app.route("/")
def index():
    return send_from_directory("localhost", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Agent 对话接口"""
    data = request.get_json()
    user_query = data.get("query", "").strip()
    history = data.get("history", [])

    if not user_query:
        return jsonify({"error": "请输入查询内容"}), 400

    # 处理上传文件（base64编码传输）
    file_data = data.get("file")
    if file_data:
        import base64
        file_bytes = base64.b64decode(file_data["data"])
        file_name = file_data["name"]
        try:
            file_text = parse_file_content(file_bytes, file_name)
            set_uploaded_file(file_text, file_name)
        except Exception as e:
            print(f"文件解析失败: {e}")

    try:
        result = run_agent(user_query=user_query, chat_history=history if history else None)
    except Exception as e:
        return jsonify({"error": f"Agent 调用失败: {str(e)}"}), 500

    response_data = {"response": result["response"]}

    from pdf_utils import get_pdfs
    pdfs = get_pdfs()
    if pdfs:
        import base64 as b64
        response_data["pdfs"] = [
            {"name": name, "data": b64.b64encode(data).decode()}
            for data, name in pdfs
        ]

    if result.get("emails"):
        response_data["emails"] = [
            {"subject": s, "body": b, "recipient": r}
            for s, b, r in result["emails"]
        ]

    return jsonify(response_data)


if __name__ == "__main__":
    print("🌊 散运助手本地服务启动: http://localhost:8899")
    app.run(host="0.0.0.0", port=8899, debug=True)
