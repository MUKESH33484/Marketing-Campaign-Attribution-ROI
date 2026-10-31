
import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import get_connection

CALCULATED_AT = datetime(2026, 10, 31, 23, 59, 59)

def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

def calculate_credit(revenue, campaign_counts):
    total_touches = sum(campaign_counts.values())
    campaign_ids = sorted(campaign_counts)

    results = []
    remaining_credit = Decimal("1.000000")
    remaining_revenue = money(revenue)

    for index, campaign_id in enumerate(campaign_ids):
        if index == len(campaign_ids) - 1:
            credit = remaining_credit
            attributed_revenue = remaining_revenue
        else:
            raw_credit = (
                Decimal(campaign_counts[campaign_id])
                / Decimal(total_touches)
            )

            credit = raw_credit.quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP
            )

            attributed_revenue = money(
                money(revenue) * raw_credit
            )

            remaining_credit -= credit
            remaining_revenue -= attributed_revenue

        results.append((
            campaign_id,
            credit,
            attributed_revenue
        ))

    return results


def main():
    connection = get_connection()

    if connection is None:
        print("Database connection failed.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM attribution_results"
        )

        if cursor.fetchone()["total"] > 0:
            print("Attribution results already exist.")
            print("Clear the existing results before recalculating.")
            return

        cursor.execute("""
            SELECT
                o.order_id,
                o.order_date,
                o.revenue,
                l.contact_id
            FROM orders o
            JOIN opportunities op
                ON o.opportunity_id = op.opportunity_id
            JOIN leads l
                ON op.lead_id = l.lead_id
            WHERE o.order_status = 'Completed'
            ORDER BY o.order_id
        """)

        orders = cursor.fetchall()

        if not orders:
            print("No completed orders found.")
            return

        insert_query = """
            INSERT INTO attribution_results (
                order_id,
                campaign_id,
                attribution_model,
                credit_percentage,
                attributed_revenue,
                calculated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        inserted = 0
        skipped = 0

        for order in orders:
            cursor.execute("""
                SELECT campaign_id, touchpoint_time, touchpoint_id
                FROM touchpoints
                WHERE contact_id = %s
                  AND touchpoint_time <= %s
                ORDER BY touchpoint_time, touchpoint_id
            """, (order["contact_id"], order["order_date"]))

            touches = cursor.fetchall()

            if not touches:
                skipped += 1
                continue

            revenue = money(order["revenue"])

            # First-Touch: earliest campaign receives all credit
            first_campaign = touches[0]["campaign_id"]

            # Last-Touch: latest campaign receives all credit
            last_campaign = touches[-1]["campaign_id"]

            models = {
                "First Touch": {first_campaign: 1},
                "Last Touch": {last_campaign: 1}
            }

            # Linear: divide credit equally across all touchpoints
            linear_counts = {}

            for touch in touches:
                campaign_id = touch["campaign_id"]
                linear_counts[campaign_id] = (
                    linear_counts.get(campaign_id, 0) + 1
                )

            models["Linear"] = linear_counts

            for model_name, campaign_counts in models.items():
                allocations = calculate_credit(
                    revenue,
                    campaign_counts
                )

                for campaign_id, credit, attributed_revenue in allocations:
                    cursor.execute(
                        insert_query,
                        (
                            order["order_id"],
                            campaign_id,
                            model_name,
                            credit,
                            attributed_revenue,
                            CALCULATED_AT
                        )
                    )
                    inserted += 1

        connection.commit()

        print("Attribution calculation completed!")
        print("Completed orders processed:", len(orders))
        print("Attribution rows inserted:", inserted)
        print("Orders skipped (no eligible touchpoints):", skipped)

    except Exception as error:
        connection.rollback()
        print("Error:", error)

    finally:
        cursor.close()
        connection.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
