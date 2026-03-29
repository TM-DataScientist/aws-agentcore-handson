import time
from bedrock_agentcore.memory import MemoryClient


client = MemoryClient(region_name="us-east-1")


memory_id = 'longterm_mem'


memory = client.create_memory(
    name=memory_id,
    strategies=[{
        "userPreferenceMemoryStrategy": {
            "name": "UserPreference",
            "namespaces": ["/users/{actorId}"]
        }
    }]
)