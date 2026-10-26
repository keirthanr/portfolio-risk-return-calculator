"""Beginner portfolio risk and return calculator using historical stock prices."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

# Four companies in different industries.
STOCKS = ["AAPL", "MSFT", "KO", "JPM"]
TRADING_DAYS = 252  # Approximate number of US stock trading days in a year.

# The weights correspond to STOCKS, and each row sums to 1 (100%).
PORTFOLIOS = {
    "Equal weight": [0.25, 0.25, 0.25, 0.25],
    "Tech focused": [0.40, 0.40, 0.10, 0.10],
    "Defensive tilt": [0.15, 0.15, 0.45, 0.25],
}


def fetch_prices(tickers):
    """Download 3 years of adjusted daily closing prices."""
    data = yf.download(tickers, period="3y", auto_adjust=True, progress=False)
    if data.empty or "Close" not in data:
        raise ValueError("No price data was downloaded. Check your internet connection.")
    prices = data["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])
    prices = prices.reindex(columns=tickers).dropna()
    if len(prices) < 60:
        raise ValueError("Not enough shared trading dates to calculate returns.")
    return prices


def calculate_metrics(daily_returns, weights):
    """Return annualised historical portfolio return, risk and diversification benefit."""
    weights = np.asarray(weights, dtype=float)
    if len(weights) != daily_returns.shape[1] or np.any(weights < 0) or not np.isclose(weights.sum(), 1):
        raise ValueError("Weights must be nonnegative, match the stocks and sum to 1.")

    mean_daily_returns = daily_returns.mean()
    covariance = daily_returns.cov()

    annual_return = float((mean_daily_returns @ weights) * TRADING_DAYS)
    annual_volatility = float(np.sqrt(weights @ covariance.to_numpy() @ weights * TRADING_DAYS))

    individual_volatility = daily_returns.std() * np.sqrt(TRADING_DAYS)
    weighted_average_risk = float(individual_volatility @ weights)
    diversification_benefit = weighted_average_risk - annual_volatility
    return {
        "Annualised return": annual_return,
        "Annualised volatility": annual_volatility,
        "Diversification benefit": diversification_benefit,
    }


def main():
    prices = fetch_prices(STOCKS)
    daily_returns = prices.pct_change().dropna()

    results = {}
    for name, weights in PORTFOLIOS.items():
        results[name] = calculate_metrics(daily_returns, weights)

    summary = pd.DataFrame.from_dict(results, orient="index")
    print("\nStock order:", ", ".join(STOCKS))
    print("Portfolio weights:")
    for name, weights in PORTFOLIOS.items():
        print(f"  {name}: {', '.join(f'{weight:.0%}' for weight in weights)}")
    print("\nHistorical annualised estimates:")
    print(summary.to_string(formatters={col: "{:.2%}".format for col in summary.columns}))
    print("\nDiversification benefit = weighted average individual-stock volatility − portfolio volatility.")
    print("Higher historical return does not guarantee higher future return.")

    output = Path("output")
    output.mkdir(exist_ok=True)
    summary.to_csv(output / "portfolio_comparison.csv")

    ax = summary.plot(
        kind="bar", y=["Annualised return", "Annualised volatility"],
        rot=0, figsize=(9, 5)
    )
    ax.set_title("Portfolio comparison (historical annualised estimates)")
    ax.set_ylabel("Rate")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    plt.tight_layout()
    plt.savefig(output / "portfolio_comparison.png", dpi=160)
    plt.show()
    print("\nSaved chart and data to the output/ folder.")


if __name__ == "__main__":
    main()
