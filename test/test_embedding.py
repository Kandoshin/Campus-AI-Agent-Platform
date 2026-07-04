from openai import OpenAI

client = OpenAI(
    api_key="sk-eDhlmtLmQDVJwXQg2807925295F440Fd81A38d89C2E20fC8",
    base_url="http://127.0.0.1:3000/v1",
)

resp = client.embeddings.create(
    model="embedding-3",
    input="这是一个 embedding 测试文本"
)

embedding = resp.data[0].embedding

print("调用成功")
print("向量维度:", len(embedding))
print("前 5 个值:", embedding[:5])