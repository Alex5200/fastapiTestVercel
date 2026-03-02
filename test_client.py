# test_client.py
import requests
import aiohttp
import asyncio

API_KEY = "dev-key-123"
BASE_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": API_KEY}


def test_upload_sync():
    with open("test.pdf", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/v1/files/upload",
            headers=HEADERS,
            files={"file": f}
        )
        print(f"Upload: {response.status_code} - {response.json()}")


async def test_upload_async():
    async with aiohttp.ClientSession() as session:
        with open("test.pdf", "rb") as f:
            data = aiohttp.FormData()
            data.add_field("file", f, filename="test.pdf")

            async with session.post(
                    f"{BASE_URL}/api/v1/files/upload",
                    headers=HEADERS,
                    data=data
            ) as response:
                print(f"Upload: {response.status} - {await response.json()}")


async def test_download(filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"{BASE_URL}/api/v1/files/{filename}",
                headers=HEADERS
        ) as response:
            if response.status == 200:
                with open("downloaded.pdf", "wb") as f:
                    f.write(await response.read())
                print("Download successful!")


async def test_list():
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"{BASE_URL}/api/v1/files",
                headers=HEADERS
        ) as response:
            print(f"List: {await response.json()}")


if __name__ == "__main__":
    # test_upload_sync()
    asyncio.run(test_list())