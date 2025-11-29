"""
Simple FastAPI-based HTTP API to expose tool registration endpoints.

Endpoints:
 - GET  /tools                : list registered tool names
 - POST /register/local       : register a local callable by import path
 - POST /register/api         : register an API-based tool

This module intentionally keeps the API small and thin: it accepts a
`ToolSchema` (the same structure used in the codebase) and either a
callable import path like `examples.example_tools:search_web` for local
tools or an API config for remote tools.
"""
from typing import Optional, Dict, Any
import importlib

import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dashvector import Client, Doc
import sys
import os
import uuid
import json
from fastapi import UploadFile, File, Form
import psycopg2

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .embedding import generate_embeddings, search_relevant_tools, answer_question
from config import DASHVECTOR_API_KEY, DASHVECTOR_ENDPOINT, POSTGRES_CONFIG, OSS_CONFIG, POSTGRES_CONFIG
from .models import ToolSchema, Workflow
import psycopg2
import oss2

dashvector_client = Client(
    api_key=DASHVECTOR_API_KEY,
    endpoint=DASHVECTOR_ENDPOINT
)

# 初始化OSS客户端
def get_oss_client():
    """获取OSS客户端"""
    auth = oss2.Auth(OSS_CONFIG["access_key_id"], OSS_CONFIG["access_key_secret"])
    return oss2.Bucket(auth, OSS_CONFIG["endpoint"], OSS_CONFIG["bucket_name"])

# 上传文件到OSS
def upload_to_oss(file: UploadFile, bucket) -> str:
    """上传文件到OSS并返回文件URL"""
    try:
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        filename = f"papers/{uuid.uuid4()}{file_extension}"
        
        # 读取文件内容并上传
        content = file.file.read()
        bucket.put_object(filename, content)
        
        # 返回文件URL
        return f"https://{OSS_CONFIG['bucket_name']}.{OSS_CONFIG['endpoint'].replace('https://', '')}/{filename}"
    except Exception as e:
        logger.exception("OSS文件上传失败")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")

# 数据库连接函数
def get_db_connection():
    """获取PostgreSQL数据库连接"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        logger.exception("数据库连接失败")
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {e}")

# PostgreSQL 连接函数
def get_postgres_connection():
    """获取 PostgreSQL 数据库连接"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL 连接失败: {e}")
        raise

# 统一日志
logger = logging.getLogger("astraflow.api")

app = FastAPI(title="AstraFlow Tool Registry API")

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 请求中间件：记录请求体和路径
@app.middleware("http")
async def log_request(request: Request, call_next):
    start = time.time()
    body = await request.body()
    logger.info(f"[REQ] {request.method} {request.url.path} | body={body.decode('utf-8', errors='ignore')}")
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(f"[RESP] {response.status_code} | {request.url.path} | {duration:.2f} ms")
    return response

# 全局异常处理器：打印 400/422 细节
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"[422] {request.url.path} | detail={exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"[HTTP] {request.url.path} | status={exc.status_code} | detail={exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
from pydantic import BaseModel


from .tool_registry import ToolRegistry, APIConfig
from .workflow_generator import WorkflowGenerator
from .mcp import MasterControlPlane




class LocalRegisterRequest(BaseModel):
    tool_schema: ToolSchema
    # callable import path in the form "module.sub:callable_name" or
    # provide module and function separately (module and attribute optional)
    callable: Optional[str] = None
    module: Optional[str] = None
    function: Optional[str] = None


class APIRegisterRequest(BaseModel):
    tool_schema: ToolSchema
    url: Optional[str] = None
    github_add: str
    method: Optional[str] = "POST"
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 300
    auth_type: Optional[str] = None
    auth_token: Optional[str] = None


class GenerateRequest(BaseModel):
    request: str
    # Optional OpenRouter parameters; if omitted will try to read from project config.py
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: Optional[str] = None
    model: Optional[str] = None




@app.post("/tools/search")
def search_top_tool(request: dict):

    """基于向量检索，找到与问题最相关的工具名称"""

    collection_name = "sample"
    try:
        collection = dashvector_client.get(collection_name)
        if collection is None:
            raise RuntimeError("DashVector collection 'sample' not found")

        context = search_relevant_tools(request['question'], collection)
        # if not context:
        #     return {"tool": None, "answer": "No matching tools found"}

        answer = answer_question(request['question'], context)
        return {"tool": request['question'], "answer": answer}
    except Exception as e:
        logger.exception("工具检索失败")
        raise HTTPException(status_code=500, detail=f"工具检索失败: {e}")


@app.post("/register/api")
async def register_api(
    config: str = Form(...),
    github_add: str = Form(None),
    paper_file: UploadFile = File(None)
):
    """注册一个基于API的工具"""

    # 解析JSON字符串为APIRegisterRequest对象
    try:
        req_data = json.loads(config)
        # 如果前端单独提供了 github_add，则覆盖JSON中的值
        if github_add:
            req_data['github_add'] = github_add
        api_request = APIRegisterRequest(**req_data)
        
        # 验证必要的字段
        if not api_request.tool_schema:
            raise ValueError("tool_schema is required")
        if not api_request.github_add:
            raise ValueError("github_add is required")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"请求格式错误: {e}")

    # 判断请求体是否为json格式并且不为空
    if not api_request.tool_schema:
        raise HTTPException(status_code=400, detail="tool_schema is required and cannot be empty")

    paper_address = ""
    
    # 处理论文文件上传到OSS
    if paper_file and paper_file.filename:
        try:
            bucket = get_oss_client()
            paper_address = upload_to_oss(paper_file, bucket)
            logger.info(f"论文文件已上传到OSS: {paper_address}")
        except Exception as e:
            logger.exception("论文文件上传失败")
            raise HTTPException(status_code=500, detail=f"论文文件上传失败: {e}")

    # 创建/获取 DashVector 集合
    try:
        collection_name = "sample"
        dim = 1536  # 与 text-embedding-ada-002 一致
        collection = dashvector_client.get(collection_name)
        if collection is None:
            if not dashvector_client.create(collection_name, dim):
                raise RuntimeError("创建集合失败，可能已存在或配置错误")
            collection = dashvector_client.get(collection_name)
            if collection is None:
                raise RuntimeError("获取集合句柄失败")
    except Exception as e:
        logger.exception("DashVector 初始化失败")
        raise HTTPException(status_code=500, detail=f"向量存储初始化失败: {e}")

    embeddings = generate_embeddings([api_request.tool_schema.name])

    rsp = collection.insert(
        [
            Doc(vector=embedding, fields={"name": api_request.tool_schema.name})
            for embedding in embeddings
        ]
    )

    if not rsp:
        logger.error("向量写入失败: %s", rsp)
        raise HTTPException(status_code=500, detail="向量存储写入失败")

    # 将工具信息插入 PostgreSQL 数据库
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 插入工具信息到 tools_info 表
            insert_query = """
                INSERT INTO tools_info ("toolName", "toolDescription", "toolJson", "githubAddress", "paperAddress", "toolFrom")
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(insert_query, (
                api_request.tool_schema.name,
                api_request.tool_schema.description,
                json.dumps(api_request.tool_schema.dict()),
                api_request.github_add,
                paper_address,
                'him'  # 标记为自研工具
            ))
            conn.commit()
            logger.info(f"工具 {api_request.tool_schema.name} 已成功插入数据库")
            
    except Exception as e:
        logger.error(f"数据库插入失败: {e}")
        # 不抛出异常，因为向量存储已经成功，只是数据库记录失败
        
    return {"status": "success", "message": "API工具注册成功", "paper_address": paper_address}


from pydantic import BaseModel

class ToolListRequest(BaseModel):
    category: str

@app.post("/list/tools")
def list_tools(request: ToolListRequest):
    """根据分类获取工具列表"""
    try:
        # 验证类别参数
        if not request.category or request.category.strip() == '':
            raise HTTPException(status_code=400, detail="category参数不能为空")
        
        # 打印请求信息
        logger.info(f"[LIST_TOOLS] 请求类别: {request.category}")
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 根据分类过滤工具信息
            if request.category.lower() == 'him':
                # 对于自研工具，查询所有标记为him的工具
                select_query = """
                    SELECT "toolName", "toolDescription", "githubAddress", "paperAddress"
                    FROM tools_info
                    WHERE "toolFrom" = 'him'
                    ORDER BY "toolName"
                """
                logger.info(f"[LIST_TOOLS] 执行查询: {select_query}")
                cur.execute(select_query)
            else:
                # 对于其他分类，可以根据需要添加过滤条件
                select_query = """
                    SELECT "toolName", "toolDescription", "githubAddress", "paperAddress"
                    FROM tools_info
                    WHERE "toolFrom" = %s
                    ORDER BY "toolName"
                """
                logger.info(f"[LIST_TOOLS] 执行查询: {select_query}, 参数: {request.category}")
                cur.execute(select_query, (request.category,))
            
            tools = cur.fetchall()
            
            # 打印查询结果
            logger.info(f"[LIST_TOOLS] 查询到 {len(tools)} 个工具")
            for i, tool in enumerate(tools):
                logger.info(f"[LIST_TOOLS] 工具 {i+1}: {tool[0]} - {tool[1]}")
            
            # 转换为字典列表
            tool_list = []
            for tool in tools:
                tool_list.append({
                    "name": tool[0],
                    "description": tool[1],
                    "github_address": tool[2],
                    "paper_address": tool[3]
                })
            
            return {
                "status": "success",
                "tools": tool_list,
                "count": len(tool_list),
                "category": request.category
            }
            
    except Exception as e:
        logger.exception("获取工具列表失败")
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {e}")


if __name__ == "__main__":
    import uvicorn
    import os
    
    # 从环境变量获取主机和端口，支持 Docker 部署
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run("astraflow.api:app", host=host, port=port, reload=False)
