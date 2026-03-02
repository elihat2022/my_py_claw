import functools
_cache_memory = {}

def response_cache(func):

    @functools.wraps(func)
    async def wrapper(self, strategy, prompt):
        strategy_name = strategy.__class__.__name__
        key_search = f"{strategy_name}_{prompt.lower().strip()}"
        # Existing prompt in cache
        if key_search in _cache_memory:
            print(f"Cache response '{prompt}'")
            return _cache_memory[key_search]
        
        # New Prompt
        print(f"Calling the API: '{prompt}'...")
        response = await func(self, strategy, prompt)
        _cache_memory[key_search] =response

        return response



    return wrapper