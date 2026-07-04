from pymilvus import MilvusClient

# 改为连接你 Docker 容器暴露出来的 19530 端口
# 如果是在 WSL 中部署且端口已映射到 localhost，直接用 localhost 即可
client = MilvusClient(uri="http://localhost:19530")

print("成功连接到 WSL Docker 中的 Milvus 服务！")

collection_name = "test_rag_collection"

# 检查 Collection 是否已存在，存在则先删除（方便反复测试）
if client.has_collection(collection_name):
    client.drop_collection(collection_name)

# 创建一个测试 Collection
client.create_collection(
    collection_name=collection_name,
    dimension=768  # 对应你后续使用的 Embedding 模型维度
)
print(f"Collection '{collection_name}' 创建成功！")