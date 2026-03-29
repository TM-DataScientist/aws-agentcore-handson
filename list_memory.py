from bedrock_agentcore.memory import MemoryClient


client = MemoryClient(region_name="us-east-1")


print("--------------------------------------------------------------------")


for memory in client.list_memories():
    print(f"Memory Arn: {memory.get('arn')}")
    print(f"Memory ID: {memory.get('id')}")
    print("--------------------------------------------------------------------")