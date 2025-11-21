# 20251121

Python implementation of a binomial option pricing model. Use the `price_option`
convenience function or the `BinomialPricer` class to value European or American
calls and puts using a recombining binomial tree.

## Quick start

```bash
python binomial.py
```

You can also import the module directly:

```python
from binomial import price_option

price = price_option(
    spot=50,
    strike=55,
    rate=0.03,
    up=1.08,
    down=0.92,
    periods=5,
    maturity=1.0,
    option_type="put",
    american=True,
)
print(price)
```
