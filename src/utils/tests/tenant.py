def gen_tenant_id() -> str:
    import random
    tid = random.randint(1, 2**32)
    return f"tenant{tid}"
