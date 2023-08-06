import requests
from tabulate import tabulate
import mandrill
from datetime import datetime, timedelta
from keys import alpha_vantage_api_key, mandrill_api_key

symbol = 'XEQT.TO'

def get_alpha_vantage_data():
    # Endpoint URL for getting the current day's data
    daily_endpoint = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={alpha_vantage_api_key}'

    try:
        # Make the API request to Alpha Vantage
        response = requests.get(daily_endpoint)
        response.raise_for_status()

        # Get the data in JSON format
        data = response.json()

        # Extract the latest date and corresponding stats
        latest_date = list(data['Time Series (Daily)'].keys())[0]
        stats = data['Time Series (Daily)'][latest_date]

        return stats

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None

    except Exception as err:
        print(f"An error occurred: {err}")
        return None

def calculate_percentage_change(closing_prices):
    # Calculate daily, weekly, monthly, and yearly percentage changes
    current_close = float(closing_prices[0])
    one_day_ago_close = float(closing_prices[1])
    one_week_ago_close = float(closing_prices[5])
    one_month_ago_close = float(closing_prices[20])
    one_year_ago_close = float(closing_prices[250])

    daily_change = (current_close - one_day_ago_close) / one_day_ago_close * 100
    weekly_change = (current_close - one_week_ago_close) / one_week_ago_close * 100
    monthly_change = (current_close - one_month_ago_close) / one_month_ago_close * 100
    yearly_change = (current_close - one_year_ago_close) / one_year_ago_close * 100

    return {
        'Daily Change (%)': f"{daily_change:.2f}%",
        'Weekly Change (%)': f"{weekly_change:.2f}%",
        'Monthly Change (%)': f"{monthly_change:.2f}%",
        'Yearly Change (%)': f"{yearly_change:.2f}%",
    }

def create_html_table(stats, title, percentage_changes):
    # Exclude 'Volume' key from stats
    if 'Volume' in stats:
        stats.pop('Volume')

    rows = []
    for key, value in stats.items():
        # Add dollar sign to the first four values
        if len(rows) < 4:
            try:
                value = float(value)
                value = f"${value:.2f}"
            except ValueError:
                pass
        rows.append([key, value])

    # Add percentage change rows
    for key, value in percentage_changes.items():
        rows.append([key, value])

    table_html = f"<h1>{title}</h1><br>" + tabulate(rows, headers=['Stat', 'Value'], tablefmt='html')

    # Add inline CSS for borders and centering
    table_html = table_html.replace('<table>', '<table style="border-collapse: collapse; width: 100%;">')
    table_html = table_html.replace('<th>', '<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">')
    table_html = table_html.replace('<td>', '<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">')
    table_html = table_html.replace('<tr>', '<tr style="border: 1px solid #ddd;">')

    return table_html


def send_email(html_content):
    mandrill_client = mandrill.Mandrill(mandrill_api_key)

    message = {
        'from_email': 'kerry@uptrendsystems.com',
        'to': [{'email': 'kerry@uptrendsystems.com'}],
        'subject': 'Stock Data',
        'html': f'<div style="font-family: Arial, sans-serif; text-align: center;">{html_content}</div>',
    }

    try:
        result = mandrill_client.messages.send(message=message)
        print("Email sent successfully!")
        print(result)
    except mandrill.Error as e:
        print(f"A mandrill error occurred: {e}")

def main():
    # Get current day's data from Alpha Vantage
    alpha_vantage_stats = get_alpha_vantage_data()

    if alpha_vantage_stats is not None:
        # Get historical data for the last 1 year from Alpha Vantage
        year_ago_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        endpoint = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={alpha_vantage_api_key}&outputsize=full'
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            closing_prices = [data['Time Series (Daily)'][date]['4. close'] for date in data['Time Series (Daily)'] if date >= year_ago_date]
            if len(closing_prices) >= 250:
                # Calculate percentage changes
                percentage_changes = calculate_percentage_change(closing_prices)
                # Create an HTML table for Alpha Vantage and percentage changes data
                table_html = create_html_table(alpha_vantage_stats, "XEQT.TO", percentage_changes)
                # Send the email with the HTML content
                send_email(table_html)
            else:
                print("Not enough data to calculate percentage changes for the last 1 year.")
        else:
            print(f"Failed to fetch historical data from Alpha Vantage. Status code: {response.status_code}")

if __name__ == "__main__":
    main()
