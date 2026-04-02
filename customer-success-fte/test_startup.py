"""Test script to check startup issues"""
import asyncio
from app.config import get_settings
from app.services.kafka_producer import kafka_producer

async def test_startup():
    print("Loading settings...")
    settings = get_settings()
    print(f"Settings loaded: {settings.environment}")
    print(f"Kafka servers: {settings.kafka_bootstrap_servers}")
    
    print("\nTesting Kafka producer start...")
    try:
        await kafka_producer.start()
        print("Kafka producer started successfully!")
        await kafka_producer.stop()
    except Exception as e:
        print(f"Kafka producer failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_startup())
