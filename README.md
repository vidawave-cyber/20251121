# 20251121

Python implementation of a binomial option pricing model. Use the `price_option`
convenience function or the `BinomialPricer` class to value European or American
calls and puts using a recombining binomial tree.

## Monte Carlo pricing with custom payoffs

If you prefer a simulation-based approach or want to experiment with bespoke
payoff shapes, run the Monte Carlo helper and enter your own payoff expression
when prompted. The terminal price is available as `s` (or `S`, `S_T`).

```bash
python monte_carlo.py
```

Example payoff inputs:

- `max(s - 100, 0)` – vanilla call
- `max(90 - s, 0)` – vanilla put
- `max(10 - abs(s - 100), 0)` – butterfly-style payoff

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
