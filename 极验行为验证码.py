from playwright.sync_api import sync_playwright
import re
import time
import requests
import base64
import os
import random
API_URL = "http://api.ttshitu.com"
def predict_base64(username, password, typeid, image_path, imageback_path=None, timeout=60, retries=3):
    """
    使用 JSON + Base64 提交识别请求。
    - 当类型需要两张图时（如：18 缺口识别、1029/2029 背景匹配旋转、1033 拖动拼图），传入 imageback_path。
    - 注意：HTTP 超时时间建议设置为 60 秒（见文档要求）。
    """
    with open(image_path, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode()
    data = {"username": username, "password": password, "typeid": str(typeid), "image": b64_image}

    if imageback_path:
        with open(imageback_path, "rb") as fb:
            data["imageback"] = base64.b64encode(fb.read()).decode()

    for attempt in range(retries):
        resp = requests.post(f"{API_URL}/predict", json=data, timeout=timeout)
        result = resp.json()
        if result.get("success"):
            # 返回示例：{"result": "AXSZ", "id": "..."}
            return result["data"]
        msg = str(result.get("message", ""))
        # 人工不足/超时等情况重试，避免脚本卡死
        if any(x in msg for x in ["人工不足", "超时", "timeout", "请延长超时时间"]):
            time.sleep(2)
            continue
        return {"error": msg}
    return {"error": "重试仍失败"}
with sync_playwright() as p:
    # 启动浏览器
    browser = p.chromium.launch(headless=False,channel="msedge")
    # 新建页面
    page = browser.new_page()
    page.goto("https://www.geetest.com/adaptive-captcha")
    # 等待页面加载完成
    page.wait_for_timeout(3000)
    a = page.locator("#gt-showZh-mobile > div > section > div > div > div.tab-left > div.base-container > div.type-config > div.tab-item.tab-item-1 ")
    a.click()
    page.wait_for_timeout(5000)
    tags = page.locator("#captcha > .geetest_captcha .geetest_btn_click")
    tags.click()
    #获取背景图片
    ele_background = page.locator(".geetest_bg ")
    back = ele_background.get_attribute("style")
    rm = re.compile(r'"(.+?)"')
    ele_url = re.findall(rm,back)[0]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"
    }
    response = requests.get(url=ele_url, headers=headers)
    t = (int(time.time()))
    with open(f"{t}.png","wb") as f:
        f.write(response.content)
    #获取图片位置
    r2 = predict_base64(username="账号",
                        password="密码",
                        typeid=33,
                        image_path=f"{t}.png")
                        # imageback_path="C:/Users/Administrator/Desktop/bottom.jpg")
    end = r2["result"]
    os.remove(f"{t}.png")
    #滑块
    page.wait_for_timeout(3000)
    #获取滑块位置
    ele_btn = page.locator(".geetest_btn")
    slider = ele_btn.bounding_box()
    start_x = slider["x"] + slider["width"] / 2
    srart_y = slider["y"] + slider["height"] / 2
    page.mouse.move(start_x, srart_y)
    end_x = int(start_x) + int(end) - 15
    x = start_x
    page.mouse.down()
    while True:

        x += random.randint(1, 15)
        work = min(x, end_x)
        page.mouse.move(work, srart_y)
        time.sleep(0.01)
        if work == end_x:
            break
    page.mouse.up()


    page.wait_for_timeout(3000000)