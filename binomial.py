"""
Binomial option pricing model implementation.

The implementation uses a Cox-Ross-Rubinstein style recombining tree with
risk-neutral probabilities. It supports European and American exercise styles
for both calls and puts.
"""
from dataclasses import dataclass
from math import exp
from typing import Literal


OptionType = Literal["call", "put"]


@dataclass
class OptionSpec:
    """Specification for a single option.

    Attributes
    ----------
    spot : float
        Current underlying asset price.
    strike : float
        Strike price of the option.
    rate : float
        Annualized continuously compounded risk-free rate.
    up : float
        Up-factor per time step (u > 1).
    down : float
        Down-factor per time step (0 < d < 1).
    periods : int
        Number of steps in the binomial tree.
    maturity : float
        Time to maturity in years.
    option_type : OptionType
        "call" for a call option, "put" for a put option.
    american : bool
        If True, price an American option; otherwise price a European option.
    """

    spot: float
    strike: float
    rate: float
    up: float
    down: float
    periods: int
    maturity: float
    option_type: OptionType = "call"
    american: bool = False


class BinomialPricer:
    """Price options using a recombining binomial tree."""

    def __init__(self, spec: OptionSpec) -> None:
        self.spec = spec
        self._validate_spec()

    def price(self) -> float:
        spec = self.spec
        dt = spec.maturity / spec.periods
        discount = exp(-spec.rate * dt)
        prob = (exp(spec.rate * dt) - spec.down) / (spec.up - spec.down)

        # Terminal asset prices and option values
        values = []
        for up_moves in range(spec.periods + 1):
            price = spec.spot * (spec.up ** up_moves) * (spec.down ** (spec.periods - up_moves))
            payoff = self._payoff(price)
            values.append(payoff)

        # Backward induction
        for step in range(spec.periods - 1, -1, -1):
            next_values = []
            for i in range(step + 1):
                continuation = discount * (prob * values[i + 1] + (1 - prob) * values[i])
                if spec.american:
                    exercise_value = self._payoff(self._asset_price(step, i))
                    node_value = max(exercise_value, continuation)
                else:
                    node_value = continuation
                next_values.append(node_value)
            values = next_values
        return values[0]

    def _payoff(self, price: float) -> float:
        if self.spec.option_type == "call":
            return max(0.0, price - self.spec.strike)
        return max(0.0, self.spec.strike - price)

    def _asset_price(self, step: int, up_moves: int) -> float:
        down_moves = step - up_moves
        return self.spec.spot * (self.spec.up ** up_moves) * (self.spec.down ** down_moves)

    def _validate_spec(self) -> None:
        spec = self.spec
        if spec.periods <= 0:
            raise ValueError("periods must be positive")
        if spec.maturity <= 0:
            raise ValueError("maturity must be positive")
        if spec.up <= 1:
            raise ValueError("up factor should be greater than 1")
        if not (0 < spec.down < 1):
            raise ValueError("down factor should be between 0 and 1")
        if spec.up <= spec.down:
            raise ValueError("up factor must exceed down factor")
        if spec.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")


def price_option(
    *,
    spot: float,
    strike: float,
    rate: float,
    up: float,
    down: float,
    periods: int,
    maturity: float,
    option_type: OptionType = "call",
    american: bool = False,
) -> float:
    """Convenience wrapper to price a single option.

    Parameters
    ----------
    spot : float
        Current underlying asset price.
    strike : float
        Strike price of the option.
    rate : float
        Annualized continuously compounded risk-free rate.
    up : float
        Up-factor per time step (u > 1).
    down : float
        Down-factor per time step (0 < d < 1).
    periods : int
        Number of steps in the binomial tree.
    maturity : float
        Time to maturity in years.
    option_type : {"call", "put"}
        Type of option to price.
    american : bool, default False
        If True, price an American option; otherwise a European option.

    Returns
    -------
    float
        The option price at the root of the binomial tree.
    """

    spec = OptionSpec(
        spot=spot,
        strike=strike,
        rate=rate,
        up=up,
        down=down,
        periods=periods,
        maturity=maturity,
        option_type=option_type,
        american=american,
    )
    return BinomialPricer(spec).price()


if __name__ == "__main__":
    example_price = price_option(
        spot=100,
        strike=100,
        rate=0.05,
        up=1.1,
        down=0.9,
        periods=3,
        maturity=1.0,
        option_type="call",
    )
    print(f"Example European call price: {example_price:.4f}")
