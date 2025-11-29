import dashscope
from dashscope import TextEmbedding
from config import DASHSCOPE_API_KEY
from dashscope import Generation
dashscope.api_key=DASHSCOPE_API_KEY


def generate_embeddings(text):
    """
    将输入文本转成 DashScope 的 text-embedding-v1 向量。
    
    参数
    ----
    text : str | list[str]
        单个文本或文本列表。

    返回
    ----
    list[float] | list[list[float]]
        如果输入是单个字符串，返回 1536 维的 float 列表；
        如果输入是字符串列表，返回与输入顺序对应的二维 float 列表（每个文本对应一个 1536 维向量）。
    """
    rsp = TextEmbedding.call(model=TextEmbedding.Models.text_embedding_v1,
                             input=text)
    
    embeddings = [record['embedding'] for record in rsp.output['embeddings']]
    return embeddings if isinstance(text, list) else embeddings[0]


# 查看下embedding向量的维数，后面使用 DashVector 检索服务时会用到，目前是1536
print(len(generate_embeddings('hello')))



def search_relevant_tools(question,collection):

    # 向量检索：指定 topk = 1 
    rsp = collection.query(generate_embeddings(question), output_fields=['name'],
                           topk=1)
    assert rsp
    return rsp.output[0].fields['name']

def answer_question(question, context):
    prompt = f'''请基于```内的内容回答问题。"
	```
	{context}
	```
	我的问题是：{question}。
    '''
    
    rsp = Generation.call(model='qwen-turbo', prompt=prompt)
    return rsp.output.text