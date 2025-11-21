"""
Monte Carlo option pricing with customizable payoffs.

This module provides a simple geometric Brownian motion simulator and allows
users to specify the payoff expression interactively. The payoff expression is
evaluated in a restricted namespace to reduce the risk of executing unsafe
code. You can also import the `monte_carlo_price` function and supply your own
callable payoff.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, sqrt
from random import gauss
from typing import Callable


Payoff = Callable[[float], float]

_ALLOWED_NAMES = {
    "exp": exp,
    "sqrt": sqrt,
    "log": log,
    "max": max,
    "min": min,
    "abs": abs,
}


@dataclass
class MonteCarloSpec:
    """Parameters for Monte Carlo option pricing.

    Attributes
    ----------
    spot : float
        Current price of the underlying asset.
    rate : float
        Annualized continuously compounded risk-free rate.
    volatility : float
        Annualized volatility of the underlying asset (sigma).
    maturity : float
        Time to maturity in years.
    dividend : float
        Continuous dividend yield. Defaults to 0.
    paths : int
        Number of simulated price paths. Defaults to 20_000.
    payoff : Payoff
        Function that maps the terminal price to a payoff.
    """

    spot: float
    rate: float
    volatility: float
    maturity: float
    dividend: float
    paths: int
    payoff: Payoff


def monte_carlo_price(spec: MonteCarloSpec) -> float:
    """Estimate an option price with Monte Carlo simulation.

    The simulation uses a single-step geometric Brownian motion under the
    risk-neutral measure and discounts the average payoff.
    """

    if spec.paths <= 0:
        raise ValueError("paths must be positive")
    if spec.spot <= 0:
        raise ValueError("spot must be positive")
    if spec.volatility <= 0:
        raise ValueError("volatility must be positive")
    if spec.maturity <= 0:
        raise ValueError("maturity must be positive")

    drift = (spec.rate - spec.dividend - 0.5 * spec.volatility ** 2) * spec.maturity
    diffusion_scale = spec.volatility * sqrt(spec.maturity)

    payoff_sum = 0.0
    for _ in range(spec.paths):
        z = gauss(0.0, 1.0)
        terminal_price = spec.spot * exp(drift + diffusion_scale * z)
        payoff_sum += spec.payoff(terminal_price)

    discounted_average = exp(-spec.rate * spec.maturity) * (payoff_sum / spec.paths)
    return discounted_average


def build_payoff(expression: str) -> Payoff:
    """Return a payoff function from a user-provided expression.

    The expression can reference the terminal price using any of ``s``, ``S``,
    or ``S_T``. Common math helpers like ``max``, ``min``, ``exp``, ``log``, and
    ``sqrt`` are available. Examples:

    - ``max(s - 100, 0)`` for a call
    - ``max(80 - S_T, 0)`` for a put
    - ``max(10 - abs(s - 100), 0)`` for a butterfly
    """

    expression = expression.strip()
    if not expression:
        raise ValueError("Payoff expression must not be empty")

    def payoff(terminal_price: float) -> float:
        local_env = {**_ALLOWED_NAMES, "s": terminal_price, "S": terminal_price, "S_T": terminal_price}
        return float(eval(expression, {"__builtins__": None}, local_env))

    return payoff


def prompt_for_spec() -> MonteCarloSpec:
    """Collect pricing inputs from the user via the command line."""

    print("Enter option parameters (press Enter to accept defaults):")
    spot = _read_float("Spot price", 100.0)
    rate = _read_float("Risk-free rate (continuously compounded)", 0.05)
    volatility = _read_float("Volatility (sigma)", 0.2)
    maturity = _read_float("Maturity in years", 1.0)
    dividend = _read_float("Dividend yield", 0.0)
    paths = int(_read_float("Number of Monte Carlo paths", 20000))

    print("\nProvide a payoff expression using s (or S, S_T) for the terminal price.")
    print("Examples: max(s - 100, 0), max(90 - s, 0), max(10 - abs(s - 100), 0)")
    expression = input("Payoff expression [max(s - 100, 0)]: ") or "max(s - 100, 0)"

    payoff = build_payoff(expression)
    return MonteCarloSpec(
        spot=spot,
        rate=rate,
        volatility=volatility,
        maturity=maturity,
        dividend=dividend,
        paths=paths,
        payoff=payoff,
    )


def _read_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} [{default}]: ").strip()
    return float(raw) if raw else default


if __name__ == "__main__":
    spec = prompt_for_spec()
    price = monte_carlo_price(spec)
    print(f"\nEstimated option price: {price:.4f}")
