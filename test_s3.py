import asyncio
import aioboto3
from config import settings


async def test_connection():
    session = aioboto3.Session()
    endpoint_url = f"https://{settings.get_s3_url()}"

    print(f"Testing connection to: {endpoint_url}")

    async with session.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            # region_name=settings.s3_region,
    ) as s3:
        try:
            # Простая проверка доступа к bucket
            await s3.put_bucket_versioning(
                Bucket=settings.s3_bucket,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            await s3.head_bucket(Bucket=settings.s3_bucket)
            print("✅ Connection successful!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {type(e).__name__}: {e}")
            return False


if __name__ == "__main__":
    asyncio.run(test_connection())