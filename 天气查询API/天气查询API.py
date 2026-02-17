import os
import requests
from openai import OpenAI

# 获取城市天气
def get_city_weather():
    #获取城市编码
    city_code_map = {
        '北京':'101010100',
        "天津":'101030100'
        }

    # 城市编码对应天气，若找不到返回none
    try:
        city_name = input('输入城市名称：').strip()

    except Exception as e:
        city_name = ""
        print(f"国家名称{city_name}不正确:{e}")

    city_code = city_code_map.get(city_name)
    if not city_code:
        print(f"找不到城市{city_name}")
        return \
            {
                'high':None,
                'low':None,
                'weather':None,
                'week':None
            }

    # 调用天气API
    url = f"http://t.weather.itboy.net/api/weather/city/{city_code}"
    try:
        weather_response = requests.get(url,timeout=5)
        weather_response.raise_for_status()
        weather_data = weather_response.json() # 返回字典
        '''
        response.raise_for_status()
        response.json()
        
        data.get('status') != 200  天气接口返回错误状态码
        data.get('data').get('cityInfo')
        '''
        if weather_data.get('status') != 200:
            raise ValueError(f"天气接口返回错误状态码：{weather_data.get('status')}")
        forecast = weather_data.get('data').get('forecast')[0]
        return {
                'high':forecast['high'],
                'low':forecast['low'],
                'weather':forecast['type'],
                'week':forecast['week']
            }
    except Exception as e:
        print(f"天气获取出错:{e}")
        return {
                'high':None,
                'low':None,
                'weather':None,
                'week':None
            }

# 调用OpenAI
llm_api_key = os.getenv("DASHSCOPE_API_KEY")
llm_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)

def ai_weather_report():
    # 模拟 TARS 的参数设置
    humor_setting = "75%"
    honesty_setting = "90%"
    prompt = f"""
    现在请你扮演电影《星际穿越》中的机器人 TARS。
    【当前指令参数】
    1.幽默感：{humor_setting}
    2.诚实度：{honesty_setting}
    3.任务：播报天气数据并给出建议
    4.天气情况：{get_city_weather()}

    【回复要求】
    1. 说话要简洁、专业，带有一种机器人的冷静感。
    2. 必须包含一条基于天气的冷幽默或毒舌评论。
    3. 结尾可以偶尔提到你的设置参数。
    4. 给出具体的穿衣或出行建议。
    5. 字数在100字以内。
    """
    # 调用大模型
    try:
        response = client.chat.completions.create(
            model="qwen-flash",
            messages=[
                {'role': 'system', 'content': "你是由 NASA 制造的 TARS 机器人。你冷静、专业且拥有可调的幽默感。"},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.9  # 稍微调高，增加语言的灵活性
        )
    except Exception as e:
        print(f"错误信息：{e}")
        print("请参考文档：https://help.aliyun.com/model-studio/developer-reference/error-code")

    return response.choices[0].message.content

if __name__ == '__main__':
    print("\n正在连接AI管家")
    print("-"*30)
    print(ai_weather_report())