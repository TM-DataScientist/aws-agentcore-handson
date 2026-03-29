from bedrock_agentcore.memory import MemoryClient


client = MemoryClient(region_name="us-east-1")
memory = client.create_memory(
   name="CustomerSupportAgentMemory",
   description="Memory for customer support conversations",
)
print(f"Memory ID: {memory.get('id')}")