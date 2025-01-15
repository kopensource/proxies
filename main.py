import time
from subprocess import getoutput

from src import DBUrls, ProxyFetcher

URLS = DBUrls(
    https = [
        'https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/https.txt', # Good, but not many
        'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt', # Good
        'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/refs/heads/main/proxies/https.txt', # Good
        'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/https.txt', # Ok
    ],
    http = [
        'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/refs/heads/main/http_checked.txt', # Good, but not many
        'https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies_anonymous/http.txt', # Good
        'https://raw.githubusercontent.com/sunny9577/proxy-scraper/refs/heads/master/generated/http_proxies.txt', # Ok
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/refs/heads/master/http.txt', # Ok
    ]
)
MAX_WORKERS = 25

proxy_fetcher = ProxyFetcher(urls=URLS)

while True:
    now = time.time()

    working = proxy_fetcher.test_proxies(
        max_workers=MAX_WORKERS,
        print_progress=True
    )

    dur = time.time() - now
    print(f"Duration: {round(dur, 2)} seconds")
    print(f"Working | http: {len(working['http'])} | https: {len(working['https'])}")

    with open('http.txt', 'w') as f:
        f.write('\n'.join(working['http']))

    with open('https.txt', 'w') as f:
        f.write('\n'.join(working['https']))

    print(getoutput('git add . && git commit -m "update" && git push'))

    time.sleep(60 * 60 * 1)
