import asyncio
import aiohttp
import aiofiles
import httpx
from tqdm import tqdm
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def check_proxy(proxy):
    try:
        async with httpx.AsyncClient(
            proxies={"http://": proxy, "https://": proxy}, timeout=30
        ) as client:
            response = await client.get(
                "https://duckduckgo.com/duckchat/v1/status",
                headers={
                    "User-Agent": "PostmanRuntime/7.39.0",
                    "Accept": "text/event-stream",
                    "x-vqd-accept": "1",
                },
            )
            response.raise_for_status()
            x_vqd_4 = response.headers.get("x-vqd-4")
            return x_vqd_4 is not None
    except Exception as e:
        logging.debug(f"代理 {proxy} 测试失败: {str(e)}")
        return False


async def load_proxies(filename):
    async with aiofiles.open(filename, mode="r") as f:
        proxies = await f.readlines()
    return [
        proxy.strip() if proxy.strip().startswith("http") else f"http://{proxy.strip()}"
        for proxy in proxies
    ]


async def load_existing_proxies(filename):
    try:
        async with aiofiles.open(filename, mode="r") as f:
            return set(await f.read().splitlines())
    except FileNotFoundError:
        return set()


async def save_successful_proxy(filename, proxy):
    async with aiofiles.open(filename, mode="a") as f:
        await f.write(f"{proxy}\n")


async def main():
    proxies = await load_proxies("proxies.txt")
    existing_proxies = await load_existing_proxies("successful_proxies.txt")
    proxies = [proxy for proxy in proxies if proxy not in existing_proxies]

    results = await asyncio.gather(
        *[check_proxy(proxy) for proxy in tqdm(proxies, desc="检查代理")]
    )

    successful_proxies = [proxy for proxy, result in zip(proxies, results) if result]

    for proxy in successful_proxies:
        if proxy not in existing_proxies:
            await save_successful_proxy("successful_proxies.txt", proxy)
            logging.info(f"代理 {proxy} 可用")

    logging.info(
        f"在测试的 {len(proxies)} 个代理中找到 {len(successful_proxies)} 个新的可用代理。"
    )


if __name__ == "__main__":
    asyncio.run(main())
