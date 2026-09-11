import os
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

# 1. 官方接口配置
# 提示：在 GitHub Actions 中，请确保你在项目的 Settings -> Secrets and variables -> Actions 中配置了 CONGRESS_API_KEY
API_KEY = os.environ.get("CONGRESS_API_KEY", "UpddHt4B3fnegURsayYA48djp2FErGYp2Q7Aw3hL")
url = f"https://congress.gov{API_KEY}&limit=20&format=json"

# 伪装高权重浏览器请求头，降低被国会 API 拦截的概率
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

reports = []

try:
    print("正在从 GitHub 环境向美国国会官方 API 发起请求...")
    response = requests.get(url, headers=headers, timeout=20)
    print(f"服务器回应状态码: {response.status_code}")
    
    # 打印前 300 个字符用于在 GitHub 部署日志中 Debug
    print(f"API 响应前缀内容: {response.text[:300]}")
    
    response.raise_for_status()
    data = response.json()
    reports = data.get("crsReports", []) 
    print(f"🎉 成功！从官方 API 获取到 {len(reports)} 条真实报告数据！")
    
except Exception as e:
    print("\n❌ 警告：API 请求失败（可能受 GitHub IP 限制或 Key 失效影响）")
    print(f"具体错误信息: {e}")
    print("将生成带有当前时间戳的“同步失败提示项”，以便您在客户端能看到脚本运行状态。\n")

# 2. 兜底测试数据（仅在 API 失败或返回为空时触发）
if not reports:
    reports = [
        {
            "title": f"【系统提示】GitHub 同步暂未获取到最新报告 (检查日志)，时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://congress.gov",
            "number": "SYNC_FAILED",
            "publishedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    ]

# 3. 构建并生成 RSS.xml
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "美国国会研究处 (CRS) 最新报告"
ET.SubElement(channel, "link").text = "https://congress.gov"
ET.SubElement(channel, "description").text = "自动同步美国国会 CRS 报告"
ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

for r in reports:
    item = ET.SubElement(channel, "item")
    
    title = r.get("title", "无标题")
    # 健壮性处理：防止官方 url 字段返回的是个复合字典对象
    url_data = r.get("url", "https://congress.gov")
    link = url_data if isinstance(url_data, str) else url_data.get("url", "https://congress.gov")
    report_id = r.get("number", "UNKNOWN_ID")
    
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link
    ET.SubElement(item, "guid", isPermaLink="false").text = report_id

    # 日期完美解析（支持带毫秒或不带毫秒的 ISO 格式）
    pub_date_raw = r.get("publishedAt", "")
    pub_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    if pub_date_raw:
        try:
            # 清理末尾的 Z 并切分毫秒
            clean_date = pub_date_raw.replace("Z", "").split(".")[0]
            pub_dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
            pub_str = pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            pass
        
    ET.SubElement(item, "pubDate").text = pub_str
    ET.SubElement(item, "description").text = f"报告编号: {report_id} | 状态: 有效"

tree = ET.ElementTree(rss)
ET.indent(tree, space=" ", level=0)
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("👉 rss.xml 已成功写出！请检查 GitHub Actions 的 commit 提交步骤。")
