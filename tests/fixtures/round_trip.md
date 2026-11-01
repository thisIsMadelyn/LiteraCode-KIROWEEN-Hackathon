# A simple greeter

This module says hello.  It is designed to be readable: the narrative
comes first, then the code follows directly below.

```python id=greet file=src/example/hello.py
def greet(name: str) -> str:
    """Return a personalised greeting."""
    return f"Hello, {name}!"
```

The main entry point calls the greeter and prints the result.

```python id=main file=src/example/hello.py
if __name__ == "__main__":
    print(greet("world"))
```

There is also a helper chunk that is not a tangle target — it exists only
for narrative clarity and merge-driver identity.

```python id=type-alias
Greeting = str
```

That is the complete module.
