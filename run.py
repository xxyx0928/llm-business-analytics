#!/usr/bin/env python3
from app import app

if __name__ == '__main__':
    print("🚀 大模型行业经营数据分析工具启动中...")
    print("📱 请在浏览器中打开: http://localhost:8080")
    print("=" * 50)
    app.run(debug=True, port=8080, host='0.0.0.0')
