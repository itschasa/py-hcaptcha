# py-hcaptcha
An unofficial wrapper for interacting with hCaptcha challenges.

# Install
* Device must be have Google Chrome installed.
```bash
pip install -U git+https://github.com/h0nde/py-hcaptcha
```

# Usage
```python
import hcaptcha

ch = hcaptcha.Challenge(
    site_key="13257c82-e129-4f09-a733-2a7cb3102832",
    site_url="https://dashboard.hcaptcha.com/",
    #proxy="user:pass@127.0.0.1:8888",
    #ssl_context=__import__("ssl")._create_unverified_context(),
    timeout=5
)

if ch.token:
    print(ch.token)
    exit()

print(ch.question["en"])

for tile in ch:
    image = tile.get_image(raw=False)
    image.show()
    if input("answer (y/n): ").lower() == "y":
        ch.answer(tile)

try:
    token = ch.submit()
    print(token)
except hcaptcha.ChallengeError as err:
    print(err)
```

# Solving
The module comes with a built-in solver, utilizing a simple bruteforce method. It may take a lot of attempts to solve a challenge, but this'll become better as the database grows.

`Solver` accepts a Redis or a dict-like object as the database parameter.

```python
import hcaptcha
from hcaptcha.solving import Solver
from itertools import cycle
import multiprocessing
from redis import Redis
import threading

WORKER_COUNT = 4
THREAD_COUNT = 50

def thread(solver, proxy_iter):
    while True:
        ch = None
        try:
            ch = hcaptcha.Challenge(
                site_key="13257c82-e129-4f09-a733-2a7cb3102832",
                site_url="https://dashboard.hcaptcha.com/",
                proxy=next(proxy_iter)
            )
            token = solver.solve(ch)
            print(token)

        except Exception as err:
            print(f"{err!r}")
        finally:
            if ch: ch.close()

def worker(proxy_list):
    proxy_iter = cycle(proxy_list)
    db = Redis()
    solver = Solver(db)

    for _ in range(THREAD_COUNT):
        threading.Thread(
            target=thread,
            args=(solver, proxy_iter)
        ).start()

if __name__ == "__main__":
    with open("proxies.txt") as fp:
        proxy_list = fp.read().splitlines()
        per = int(len(proxy_list) / WORKER_COUNT)
    
    for num in range(WORKER_COUNT):
        multiprocessing.Process(
            target=worker,
            args=(proxy_list[per * num : per * (num + 1)],)
        ).start()
```
