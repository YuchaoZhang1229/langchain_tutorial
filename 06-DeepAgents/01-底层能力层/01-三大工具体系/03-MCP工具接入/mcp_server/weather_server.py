from fastmcp import FastMCP

"""
    天气MCP服务器（流式 HTTP 传输）
    http 传输（也称为 streamable-http ）使用 HTTP 请求进行客户端-服务器通信
"""

WEATHER_DATA = {
    "北京": {"condition": "晴", "temperature": 26, "humidity": 40},
    "上海": {"condition": "多云", "temperature": 29, "humidity": 65},
    "广州": {"condition": "小雨", "temperature": 31, "humidity": 78},
    "深圳": {"condition": "雷阵雨", "temperature": 30, "humidity": 80},
}


mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """获取城市location的天气信息."""
    city = location.strip()
    weather = WEATHER_DATA.get(city)
    if weather is None:
        supported_cities = "、".join(WEATHER_DATA)
        return f"暂无 {city or '该城市'} 的示例天气数据，支持：{supported_cities}"
    return (
        f"{city}：{weather['condition']}，{weather['temperature']}°C，"
        f"相对湿度 {weather['humidity']}%"
    )

if __name__ == "__main__":
    mcp.run(transport="streamable-http",host="127.0.0.1", port=8001)
