"""
结合了Function Calling功能与数据库操作，核心功能是将用户的中文问题自动转换为SQL查询并返回结构化结果。
"""
import os
import json
import sqlite3


# 假设你已有 models 模块，这里为了演示，我们模拟一个简单的客户端
# 由于原代码引用了 models 中的阿里云模型，我们保留原样，但可替换为任何 LLM
# 为了演示，我们仍然使用阿里云（或改为 deepseek）—— 但用户只要求改数据库，模型部分不变。


from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

# ---------- 数据库初始化函数（在内存中建表和插入数据） ----------
def init_database():
    """创建内存数据库并插入示例数据，返回连接和游标"""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 建表
    schema = """
    CREATE TABLE IF NOT EXISTS Classes (
        class_id INTEGER PRIMARY KEY,
        class_name TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS Students (
        student_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        class_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS Scores (
        score_id INTEGER PRIMARY KEY,
        student_id INTEGER,
        subject TEXT NOT NULL,
        score REAL NOT NULL
    );
    """
    for stmt in schema.split(';'):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)

    # 插入数据
    insert_data = {
        "classes": [(1, '一班'), (2, '二班'), (3, '三班'), (4, '四班'), (5, '五班')],
        "students": [(1, '张三', 1), (2, '李四', 1), (3, '王五', 2), (4, '赵六', 3), (5, '钱七', 4)],
        "scores": [(1, 1, '数学', 85.5), (2, 1, '英语', 90.0), (3, 2, '数学', 78.0), (4, 3, '英语', 88.5), (5, 4, '数学', 92.0)]
    }
    for table, rows in insert_data.items():
        placeholders = ','.join(['?'] * len(rows[0]))  # 自动生成占位符
        sql = f"INSERT INTO {table} VALUES ({placeholders})"
        cursor.executemany(sql, rows)
    conn.commit()
    return conn, cursor

# ---------- 初始化数据库 ----------
conn, cursor = init_database()

# ---------- 定义数据库架构描述（供 LLM 参考） ----------
database_schema_string = """
CREATE TABLE Classes (
    class_id INTEGER PRIMARY KEY,
    class_name TEXT NOT NULL
);
CREATE TABLE Students (
    student_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    class_id INTEGER
);
CREATE TABLE Scores (
    score_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    subject TEXT NOT NULL,
    score REAL NOT NULL
);
"""

# ---------- LLM 调用函数（从原代码复制，未改动） ----------
def get_sql_completion(messages):
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,
        temperature=0,
        tools=[{
            "type": "function",
            "function": {
                "name": "ask_database",
                "description": "查询数据库的函数。输出是数据库中表的记录",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"""
                            一个SQL查询，这个SQL查询提取信息以回答用户的问题。
                            SQL应该使用这个数据库架构来编写:
                            {database_schema_string}
                            SQL查询查询应以纯文本形式返回，而不是JSON格式。
                            查询应仅包含SQLite支持的语法.
                            """,
                        }
                    },
                    "required": ["query"],
                }
            }
        }],
    )
    return response.choices[0].message

# ---------- 执行 SQL 查询的工具函数（使用 SQLite 游标） ----------
def ask_database(query):
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        # 将结果转为列表（每行为字典，方便显示）
        return [dict(row) for row in records]
    except sqlite3.Error as e:
        return f"SQL 执行错误: {e}"

# ---------- 主流程 ----------
prompt = "查询一班的学生数学成绩是多少？"
messages = [
    {"role": "system", "content": "基于表回答用户问题"},
    {"role": "user", "content": prompt}
]

response = get_sql_completion(messages)
messages.append(response)
print("LLM 首次回复:", response)

if response.tool_calls is not None:
    tool_call = response.tool_calls[0]
    if tool_call.function.name == "ask_database":
        arguments = tool_call.function.arguments
        args = json.loads(arguments)
        print("====生成 SQL====")
        print(args["query"])
        result = ask_database(args["query"])
        print("====数据库查询结果====")
        print(result)

        messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": "ask_database",
            "content": str(result)
        })
        final_response = get_sql_completion(messages)
        print("====最终回复====")
        print(final_response.content)

# 可选：关闭连接（程序结束自动关闭）
conn.close()