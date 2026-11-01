# Scenario A demo

The parser comes first in our narrative.

```python id=parse file=src/demo/main.py
def parse(text):
    return text.split()
```

Then we validate the tokens.

```python id=validate file=src/demo/main.py
def validate(tokens):
    return [t for t in tokens if t.isalpha()]
```

Finally we format the output.

```python id=fmt file=src/demo/main.py
def fmt(tokens):
    return ", ".join(tokens)
```

This is the complete pipeline: parse → validate → format.
