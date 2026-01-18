# import asyncio
# import random

# COLORS = (
#     "\033[0m",  # End of color
#     "\033[36m",  # Cyan
#     "\033[91m",  # Red
#     "\033[35m",  # Magenta
# )


# async def main():
#     return await asyncio.gather(
#         makerandom(1, 9),
#         makerandom(2, 8),
#         makerandom(3, 8),
#     )


# async def makerandom(delay, threshold=6):
#     color = COLORS[delay]
#     print(f"{color}Initiated makerandom({delay}).")
#     while (number := random.randint(0, 10)) <= threshold:
#         print(f"{color}makerandom({delay}) == {number} too low; retrying.")
#         await asyncio.sleep(delay)
#     print(f"{color}---> Finished: makerandom({delay}) == {number}" + COLORS[0])
#     return number


# if __name__ == "__main__":
#     random.seed(444)
#     r1, r2, r3 = asyncio.run(main())
#     print()
#     print(f"r1: {r1}, r2: {r2}, r3: {r3}")


# import asyncio
# import random
# import time


# async def main():
#     user_ids = [1, 2, 3]
#     start = time.perf_counter()
#     await asyncio.gather(*(get_user_with_posts(user_id) for user_id in user_ids))
#     end = time.perf_counter()
#     print(f"\n==> Total time: {end - start:.2f} seconds")


# async def get_user_with_posts(user_id):
#     user = await fetch_user(user_id)
#     await fetch_posts(user)


# async def fetch_user(user_id):
#     delay = random.uniform(0.5, 2.0)
#     print(f"User coro: fetching user by {user_id=}...")
#     await asyncio.sleep(delay)
#     user = {"id": user_id, "name": f"User{user_id}"}
#     print(f"User coro: fetched user with {user_id=} (done in {delay:.1f}s).")
#     return user


# async def fetch_posts(user):
#     delay = random.uniform(0.5, 2.0)
#     print(f"Post coro: retrieving posts for {user['name']}...")
#     await asyncio.sleep(delay)
#     posts = [f"Post {i} by {user['name']}" for i in range(1, 3)]
#     print(
#         f"Post coro: got {len(posts)} posts by {user['name']}"
#         f" (done in {delay:.1f}s):"
#     )
#     for post in posts:
#         print(f" - {post}")


# if __name__ == "__main__":
#     random.seed(444)
#     asyncio.run(main())

# import asyncio
# import random
# import time


# async def main():
#     queue = asyncio.Queue()
#     user_ids = [1, 2, 3]
#     start = time.perf_counter()
#     await asyncio.gather(
#         producer(queue, user_ids),
#         *(consumer(queue) for _ in user_ids),
#     )
#     end = time.perf_counter()
#     print(f"\n==> Total time: {end - start:.2f} seconds")


# async def producer(queue, user_ids):
#     async def fetch_user(user_id):
#         delay = random.uniform(0.5, 2.0)
#         print(f"Producer: fetching user by {user_id=}...")
#         await asyncio.sleep(delay)
#         user = {"id": user_id, "name": f"User{user_id}"}
#         print(f"Producer: fetched user with {user_id=} (done in {delay:.1f}s)")
#         await queue.put(user)
#     await asyncio.gather(*(fetch_user(uid) for uid in user_ids))
#     for _ in range(len(user_ids)):
#         await queue.put(None)  # Sentinels for consumers to terminate


# async def consumer(queue):
#     while True:
#         user = await queue.get()
#         if user is None:
#             break
#         delay = random.uniform(0.5, 2.0)
#         print(f"Consumer: retrieving posts for {user['name']}...")
#         await asyncio.sleep(delay)
#         posts = [f"Post {i} by {user['name']}" for i in range(1, 3)]
#         print(
#             f"Consumer: got {len(posts)} posts by {user['name']}"
#             f" (done in {delay:.1f}s):"
#         )
#         for post in posts:
#             print(f"  - {post}")


# if __name__ == "__main__":
#     random.seed(444)
#     asyncio.run(main())


# import asyncio


# async def powers_of_two(stop=10):
#     exponent = 0
#     while exponent < stop:
#         yield 2**exponent
#         exponent += 1
#         await asyncio.sleep(0.2)  # Simulate some asynchronous work


# async def main():
#     g = []
#     async for i in powers_of_two(5):
#         g.append(i)
#     print(g)
#     f = [j async for j in powers_of_two(5) if not (j // 3 % 5)]
#     print(f)


# asyncio.run(main())
# # [1, 2, 4, 8, 16]
# # [1, 2, 16]


# import asyncio

# async def coro(numbers):
#     await asyncio.sleep(min(numbers))
#     return list(reversed(numbers))

# async def main():
#     task = asyncio.create_task(coro([3, 2, 1]))
#     print(f"{type(task) = }")
#     print(f"{task.done() = }")
#     return await task

# result = asyncio.run(main())
# # type(task) = <class '_asyncio.Task'>
# # task.done() = False
# print(f"result: {result}")
# # # result: [1, 2, 3]


from dataclasses import dataclass
from typing import Protocol, Tuple


# =========================
# VALUES (plain data only)
# =========================
@dataclass(frozen=True)
class Order:
    bread: str
    meat: str
    greens: Tuple[str, ...] = ()
    condiments: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Sandwich:
    bread: str
    meat: str
    greens: Tuple[str, ...]
    condiments: Tuple[str, ...]
    made_by: str  # metadata added by the kitchen


# ==========================================
# WHAT (the contract) — tiny, value-only API
# ==========================================
class SandwichMaker(Protocol):
    def make(self, order: Order) -> Sandwich: ...

    # Note: No steps/tools/order of operations here.


# ===========================
# WHY (policy) — simple rules
# ===========================
def validate(order: Order) -> None:
    if "jam" in order.condiments and "mustard" in order.condiments:
        raise ValueError("Jam and mustard together? No thanks.")
    if order.bread not in {"wheat", "white", "rye"}:
        raise ValueError("Unsupported bread type.")


# ===========================================
# HOW (implementations) — different kitchens
# ===========================================
class DeliKitchen:
    def make(self, order: Order) -> Sandwich:
        # This kitchen might toast first, slice diagonally, etc. (hidden details)
        return Sandwich(
            bread=order.bread,
            meat=order.meat,
            greens=order.greens,
            condiments=order.condiments,
            made_by="deli",
        )


class RobotKitchen:
    def make(self, order: Order) -> Sandwich:
        # Different internal sequence/tools than the deli (also hidden)
        return Sandwich(
            bread=order.bread,
            meat=order.meat,
            greens=order.greens,
            condiments=order.condiments,
            made_by="robot",
        )


# ===========================================
# COMPOSE (wire WHAT + HOW at the edges)
# ===========================================
def serve(maker: SandwichMaker, order: Order) -> Sandwich:
    validate(order)  # WHY stays separate, still only values
    return maker.make(order)  # depends on WHAT (protocol), not on a concrete class


# ==========================
# EXAMPLE (try both HOWs)
# ==========================
order = Order(bread="wheat", meat="turkey", greens=("lettuce",), condiments=("mayo",))

print(serve(DeliKitchen(), order))  # Sandwich(..., made_by='deli')
print(serve(RobotKitchen(), order))  # Sandwich(..., made_by='robot')
