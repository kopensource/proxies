from typing import NamedTuple, Optional
from concurrent.futures import ThreadPoolExecutor

import requests


ProxyListCheckResult = NamedTuple(
    'ProxyListCheckResult',
    [
        ('working',  list[str]),
        ('failed',   list[str]),
        ('untested', list[str])
    ]
)

class DBUrls:
    http: list[str] = []
    https: list[str] = []

    def __init__(
        self,
        http: list[str],
        https: list[str]
    ):
        self.http = http
        self.https = https


class ProxyFetcher:
    urls: DBUrls
    test_url: str


    def __init__(
        self,
        urls: DBUrls,
        test_url: str = "https://httpbin.org/ip"
    ):
        self.urls = urls
        self.test_url = test_url


    # Public

    def test_proxies(
        self,
        max_workers: int = 20,
        timeout:     int = 10,

        print_progress: bool = False
    ) -> dict[str, list[str]]:
        working: dict[str, list[str]] = {}

        for protocol in ["https", "http"]:
            db_urls = self.urls.__getattribute__(protocol)
            proxies = self._fetch_proxies(db_urls, protocol)
            working[protocol] = [
                p.split("//")[1] for p in self._test_proxies(
                    proxy_list=proxies,
                    test_url=self.test_url,
                    max_workers=max_workers,
                    timeout=timeout,
                    print_progress=print_progress
                ).working
            ]

        return working

    def _fetch_proxies(
        self,
        urls: list[str],
        protocol: str
    ) -> list[str]:
        all_proxies_cache: set[str] = set()
        all_proxies: list[str] = []

        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status() # Raise an error for bad responses

                for proxy_base in response.text.split('\n'):
                    _proxy_base = proxy_base.strip()

                    if len(_proxy_base) == 0:
                        continue

                    _proxy_base = f"http://{_proxy_base}"

                    if _proxy_base in all_proxies_cache:
                        continue

                    all_proxies_cache.add(_proxy_base)
                    all_proxies.append(_proxy_base)
            except requests.RequestException as e:
                print(f"Error fetching file: {e}")

        _all_proxies = all_proxies
        # random.shuffle(_all_proxies)

        return _all_proxies

    def _test_proxies(
        self,

        proxy_list:  list[str],
        test_url:    Optional[str] = None,
        max_workers: int = 20,
        timeout:     int = 10,

        print_progress: bool = False
    ) -> ProxyListCheckResult:
        test_url = test_url or self.test_url

        tested_proxies  = []
        failed_proxies  = []
        working_proxies = []
        i: int = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(lambda proxy: (proxy, self._test_proxy(proxy, test_url, timeout)), proxy_list)

            for proxy, is_working in results:
                # print(f'{proxy} | {is_working}')
                tested_proxies.append(proxy)

                if is_working:
                    working_proxies.append(proxy)
                else:
                    failed_proxies.append(proxy)

                if print_progress and i % max_workers == 0:
                    print(f'ALL: {len(proxy_list)} | TESTED: {len(tested_proxies)} | WORKING: {len(working_proxies)}')

                i += 1

        if print_progress:
            print(f'ALL: {len(proxy_list)} | TESTED: {len(tested_proxies)} | WORKING: {len(working_proxies)}')

        return ProxyListCheckResult(
            working=working_proxies,
            failed=failed_proxies,
            untested=[
                p for p in proxy_list if p not in tested_proxies
            ]
        )


    # Private

    def _test_proxy(
        self,

        proxy:    str,
        test_url: str,
        timeout:  int = 5
    ) -> bool:
        try:
            response = requests.get(test_url, proxies={
                "http":  proxy,
                "https": proxy,
            }, timeout=timeout)

            response.raise_for_status()

            return True
            # return response.status_code == 200
        except requests.RequestException:
            return False
