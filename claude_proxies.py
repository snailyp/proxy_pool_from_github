import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_proxy(proxy, timeout, test_urls):
    proxies = {"http": proxy, "https": proxy}
    for url in test_urls:
        try:
            response = requests.get(url, proxies=proxies, timeout=timeout)
            if response.status_code == 200:
                return proxy, True, response.elapsed.total_seconds()
        except requests.RequestException as e:
            logging.debug(f"Proxy {proxy} failed for {url}: {str(e)}")
    return proxy, False, None

def main(input_file, output_file, max_workers, timeout, test_urls):
    with open(input_file, "r") as file:
        proxies = [proxy.strip() for proxy in file.readlines()]

    successful_proxies = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(check_proxy, proxy, timeout, test_urls) for proxy in proxies]
        
        for future in tqdm(as_completed(futures), total=len(proxies), desc="Checking proxies"):
            proxy, is_successful, response_time = future.result()
            if is_successful:
                successful_proxies.append((proxy, response_time))
                logging.info(f"Proxy {proxy} can access the site(s). Response time: {response_time:.2f}s")

    successful_proxies.sort(key=lambda x: x[1])  # 按响应时间排序

    with open(output_file, "w") as file:
        for proxy, response_time in successful_proxies:
            file.write(f"{proxy},{response_time:.2f}\n")

    logging.info(f"Found {len(successful_proxies)} working proxies out of {len(proxies)} tested.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check proxies for accessibility.")
    parser.add_argument("--input", default="success_proxies.txt", help="Input file containing proxies")
    parser.add_argument("--output", default="accessible_proxies.txt", help="Output file for working proxies")
    parser.add_argument("--workers", type=int, default=10, help="Number of worker threads")
    parser.add_argument("--timeout", type=float, default=5, help="Timeout for each request in seconds")
    parser.add_argument("--urls", nargs="+", default=["https://claude3.free2gpt.xyz/"], help="URLs to test against")
    
    args = parser.parse_args()
    
    main(args.input, args.output, args.workers, args.timeout, args.urls)