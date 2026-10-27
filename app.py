from flask import Flask, render_template
import yfinance as yf
from datetime import datetime
import time

app = Flask(__name__)


# ---------------------------------------------------------
# GET STOCK SYMBOLS FROM YAHOO FINANCE SCREENER
# ---------------------------------------------------------
def get_symbols():
    query = yf.EquityQuery(
        "and",
        [
            yf.EquityQuery("eq", ["region", "us"]),
            yf.EquityQuery("gte", ["intradayprice", 2]),
            yf.EquityQuery("lte", ["intradayprice", 10]),
            yf.EquityQuery("gt", ["percentchange", 0])
        ]
    )

    # Try Yahoo Finance screener a few times
    for attempt in range(3):
        try:
            result = yf.screen(
                query,
                sortField="percentchange",
                sortAsc=False,
                size=250
            )

            quotes = result.get("quotes", [])

            symbols = []

            for stock in quotes:
                symbol = stock.get("symbol")

                if symbol:
                    symbols.append(symbol)

            return symbols

        except Exception as e:
            print(f"Screening attempt {attempt + 1} failed: {e}")

            if attempt < 2:
                time.sleep(2)

    print("Unable to connect to Yahoo Finance.")
    return []


# ---------------------------------------------------------
# GET NEWS FOR A STOCK
# ---------------------------------------------------------
def get_news(symbol):
    try:
        ticker = yf.Ticker(symbol)

        news = ticker.news

        if news:
            first_news = news[0]

            content = first_news.get("content", {})

            title = content.get(
                "title",
                "No news available"
            )

            return title

        return "No recent news"

    except Exception as e:
        print(f"News unavailable for {symbol}: {e}")
        return "News unavailable"


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------
@app.route("/")
def home():

    stocks = []

    # Get symbols from Yahoo Finance screener
    symbols = get_symbols()

    print(f"Found {len(symbols)} stocks from screener.")

    # -----------------------------------------------------
    # Process stocks
    # -----------------------------------------------------
    for symbol in symbols:

        try:
            ticker = yf.Ticker(symbol)

            # Get basic information
            info = ticker.fast_info

            price = info.last_price
            previous_close = info.previous_close

            # Check if price data exists
            if price is None or previous_close is None:
                continue

            if previous_close == 0:
                continue

            # Calculate percentage change
            change = (
                (price - previous_close)
                / previous_close
            ) * 100

            # -------------------------------------------------
            # Our scanner conditions
            # Price between $2 and $10
            # Positive percentage change
            # -------------------------------------------------
            if 2 <= price <= 10 and change > 0:

                # Get additional information
                try:
                    company_info = ticker.info

                    float_shares = company_info.get(
                        "floatShares",
                        0
                    )

                    country = company_info.get(
                        "country",
                        "N/A"
                    )

                except Exception:
                    float_shares = 0
                    country = "N/A"

                stocks.append({
                    "symbol": symbol,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "float": float_shares,
                    "country": country,
                    "news": get_news(symbol)
                })

        except Exception as e:

            print(
                f"Error loading {symbol}: {e}"
            )

            continue

    # ---------------------------------------------------------
    # Sort by highest percentage change
    # ---------------------------------------------------------
    stocks.sort(
        key=lambda x: x["change"],
        reverse=True
    )

    # ---------------------------------------------------------
    # Display only top 3 stocks
    # ---------------------------------------------------------
    top_stocks = stocks[:3]

    # Current scan time
    scan_time = datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )

    return render_template(
        "index.html",
        stocks=top_stocks,
        scan_time=scan_time
    )


# ---------------------------------------------------------
# RUN FLASK APPLICATION
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(
        debug=True
    )