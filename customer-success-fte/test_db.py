import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            user='postgres',
            host='localhost',
            port=5433,
            database='customer_success'
        )
        print('✅ Connection successful!')
        result = await conn.fetchval('SELECT 1')
        print(f'Query result: {result}')
        await conn.close()
    except Exception as e:
        print(f'❌ Connection failed: {e}')

asyncio.run(test())
