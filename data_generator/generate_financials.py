
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta, time

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_connection

SEED = 20261022
random.seed(SEED)

AS_OF = datetime(2026, 10, 31, 23, 59, 59)


def generate_financials():

    connection = get_connection()

    if connection is None:
        print("MySQL connection failed.")
        return

    cursor = connection.cursor()

    try:
        # Prevent duplicate insertion
        for table in ["cost_records", "orders"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")

            if cursor.fetchone()[0] > 0:
                print(f"{table} already contains data. Stopping.")
                return

        # Fetch campaign budgets and dates
        cursor.execute("""
            SELECT
                campaign_id,
                budget,
                currency,
                start_date,
                end_date
            FROM campaigns
        """)

        campaigns = cursor.fetchall()

        # Fetch available campaign channels
        cursor.execute("""
            SELECT campaign_id, channel_id
            FROM campaign_channels
        """)

        campaign_channels = {}

        for campaign_id, channel_id in cursor.fetchall():
            campaign_channels.setdefault(
                campaign_id, []
            ).append(channel_id)

        cost_records = []
        cost_number = 1

        cost_types = [
            "Paid Advertising",
            "Content Production",
            "Email Marketing",
            "Agency Fee",
            "Analytics"
        ]

        # Generate campaign expenses
        for campaign in campaigns:

            campaign_id, budget, currency, start_date, end_date = campaign

            latest_date = min(
                datetime.combine(end_date, time.max),
                AS_OF
            )

            earliest_date = datetime.combine(
                start_date, time.min
            )

            if earliest_date > latest_date:
                continue

            seconds = int(
                (latest_date - earliest_date).total_seconds()
            )

            # Keep total expenses below the campaign budget
            expense_percentage = random.uniform(0.25, 0.60)
            total_expense = round(
                float(budget) * expense_percentage, 2
            )

            first_expense = round(
                total_expense * random.uniform(0.35, 0.65), 2
            )

            expense_amounts = [
                first_expense,
                round(total_expense - first_expense, 2)
            ]

            for amount in expense_amounts:

                incurred_at = earliest_date + timedelta(
                    seconds=random.randint(0, seconds)
                )

                available_channels = campaign_channels.get(
                    campaign_id, []
                )

                channel_id = (
                    random.choice(available_channels)
                    if available_channels else None
                )

                cost_records.append((
                    f"CST-2026-{cost_number:06d}",
                    campaign_id,
                    channel_id,
                    random.choice(cost_types),
                    amount,
                    currency,
                    incurred_at,
                    "Synthetic campaign expense record"
                ))

                cost_number += 1

        # Insert campaign costs
        cursor.executemany("""
            INSERT INTO cost_records
            (cost_id, campaign_id, channel_id, cost_type,
             amount, currency, incurred_at, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, cost_records)

        # Fetch closed-won opportunities
        cursor.execute("""
            SELECT
                opportunity_id,
                amount,
                currency,
                closed_at
            FROM opportunities
            WHERE stage = 'Closed Won'
              AND closed_at IS NOT NULL
        """)

        won_opportunities = cursor.fetchall()

        order_records = []

        for i, opportunity in enumerate(
            won_opportunities, start=1
        ):

            opportunity_id, amount, currency, closed_at = opportunity

            order_records.append((
                f"ORD-2026-{i:06d}",
                opportunity_id,
                closed_at,
                amount,
                currency,
                "Completed"
            ))

        # Insert completed sales orders
        if order_records:
            cursor.executemany("""
                INSERT INTO orders
                (order_id, opportunity_id, order_date,
                 revenue, currency, order_status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, order_records)

        connection.commit()

        print("\nFinancial data generated successfully!")
        print("Campaign expense records:", len(cost_records))
        print("Closed-won opportunities:", len(won_opportunities))
        print("Completed sales orders:", len(order_records))

        if not order_records:
            print(
                "No closed-won opportunities were available. "
                "No sales orders were created."
            )

    except Exception as error:
        connection.rollback()
        print("Financial data generation failed:", error)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_financials()
