"""Web server for Monte Carlo option pricing."""
from __future__ import annotations

from typing import Dict, Mapping, Tuple
from flask import Flask, request, render_template_string, jsonify

from monte_carlo import MonteCarloSpec, build_payoff, monte_carlo_price


app = Flask(__name__)

DEFAULTS: Dict[str, float] = {
    "spot": 100.0,
    "rate": 0.05,
    "volatility": 0.2,
    "maturity": 1.0,
    "dividend": 0.0,
    "paths": 20000,
}


FORM_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Monte Carlo Option Pricer</title>
    <style>
      body { font-family: system-ui, -apple-system, sans-serif; margin: 2rem; line-height: 1.5; }
      form { max-width: 640px; display: grid; gap: 0.75rem; }
      label { display: flex; flex-direction: column; font-weight: 600; }
      input { padding: 0.45rem 0.5rem; font-size: 1rem; }
      .error { color: #b00020; }
      .result { margin-top: 1rem; padding: 0.75rem; background: #f3f6ff; border-left: 4px solid #2d5cf6; }
    </style>
  </head>
  <body>
    <h1>Monte Carlo Option Calculator</h1>
    <p>Simulate a single-step geometric Brownian motion under the risk-neutral measure. Provide your own payoff expression using <code>s</code> (or <code>S</code>, <code>S_T</code>) for the terminal price.</p>
    <form method="post">
      <label>Spot price
        <input type="number" step="any" name="spot" value="{{ values.spot }}" required>
      </label>
      <label>Risk-free rate (r)
        <input type="number" step="any" name="rate" value="{{ values.rate }}" required>
      </label>
      <label>Volatility (sigma)
        <input type="number" step="any" name="volatility" value="{{ values.volatility }}" required>
      </label>
      <label>Maturity (years)
        <input type="number" step="any" name="maturity" value="{{ values.maturity }}" required>
      </label>
      <label>Dividend yield
        <input type="number" step="any" name="dividend" value="{{ values.dividend }}" required>
      </label>
      <label>Monte Carlo paths
        <input type="number" step="1" name="paths" value="{{ values.paths }}" min="1" required>
      </label>
      <label>Payoff expression
        <input type="text" name="payoff" value="{{ values.payoff }}" required>
      </label>
      <button type="submit">Price option</button>
    </form>

    {% if errors %}
      <div class="error">
        <h3>Input issues</h3>
        <ul>
          {% for error in errors %}
            <li>{{ error }}</li>
          {% endfor %}
        </ul>
      </div>
    {% endif %}

    {% if price is not none %}
      <div class="result">
        <strong>Estimated option price:</strong> {{ price|round(4) }}
      </div>
    {% endif %}
  </body>
</html>
"""


def parse_spec(source: Mapping[str, str]) -> Tuple[MonteCarloSpec, Dict[str, float | str]]:
    """Convert incoming data to a MonteCarloSpec and echo values for the form."""

    values: Dict[str, float | str] = {}

    def _get_float(name: str, default: float) -> float:
        raw = source.get(name)
        if raw is None or raw == "":
            values[name] = default
            return default
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name.replace('_', ' ').title()} must be numeric") from exc
        values[name] = value
        return value

    spot = _get_float("spot", DEFAULTS["spot"])
    rate = _get_float("rate", DEFAULTS["rate"])
    volatility = _get_float("volatility", DEFAULTS["volatility"])
    maturity = _get_float("maturity", DEFAULTS["maturity"])
    dividend = _get_float("dividend", DEFAULTS["dividend"])
    paths_value = source.get("paths", "")
    if paths_value == "":
        paths = int(DEFAULTS["paths"])
    else:
        try:
            paths = int(float(paths_value))
        except (TypeError, ValueError) as exc:
            raise ValueError("Paths must be an integer") from exc
    values["paths"] = paths

    expression = source.get("payoff", "") or "max(s - 100, 0)"
    try:
        payoff = build_payoff(expression)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    values["payoff"] = expression

    return (
        MonteCarloSpec(
            spot=spot,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
            dividend=dividend,
            paths=paths,
            payoff=payoff,
        ),
        values,
    )


@app.route("/", methods=["GET", "POST"])
def price_form():
    errors = []
    price = None
    values: Dict[str, float | str] = {**DEFAULTS, "payoff": "max(s - 100, 0)"}

    if request.method == "POST":
        try:
            spec, values = parse_spec(request.form)
            price = monte_carlo_price(spec)
        except ValueError as exc:
            errors.append(str(exc))

    return render_template_string(FORM_TEMPLATE, price=price, errors=errors, values=values)


@app.post("/api/price")
def api_price():
    data = request.get_json(silent=True) or request.form
    try:
        spec, _ = parse_spec(data)
        price = monte_carlo_price(spec)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"price": price})


if __name__ == "__main__":
    app.run(debug=True, port=8000)
