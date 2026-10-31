
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import get_connection


def calculate_roi(revenue, spend):
    if spend <= 0:
        return None

    return ((revenue - spend) / spend) * 100


def main():
    connection = get_connection()

    if connection is None:
        print("Database connection failed.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT
                c.campaign_id,
                c.campaign_name,
                c.currency,
                COALESCE(spend.total_spend, 0) AS total_spend,
                COALESCE(first_touch.revenue, 0) AS first_touch_revenue,
                COALESCE(last_touch.revenue, 0) AS last_touch_revenue,
                COALESCE(lin.revenue, 0) AS linear_revenue

            FROM campaigns c

            LEFT JOIN (
                SELECT
                    campaign_id,
                    SUM(amount) AS total_spend
                FROM cost_records
                GROUP BY campaign_id
            ) AS spend
                ON c.campaign_id = spend.campaign_id

            LEFT JOIN (
                SELECT
                    campaign_id,
                    SUM(attributed_revenue) AS revenue
                FROM attribution_results
                WHERE attribution_model = 'First Touch'
                GROUP BY campaign_id
            ) AS first_touch
                ON c.campaign_id = first_touch.campaign_id

            LEFT JOIN (
                SELECT
                    campaign_id,
                    SUM(attributed_revenue) AS revenue
                FROM attribution_results
                WHERE attribution_model = 'Last Touch'
                GROUP BY campaign_id
            ) AS last_touch
                ON c.campaign_id = last_touch.campaign_id

            LEFT JOIN (
                SELECT
                    campaign_id,
                    SUM(attributed_revenue) AS revenue
                FROM attribution_results
                WHERE attribution_model = 'Linear'
                GROUP BY campaign_id
            ) AS lin
                ON c.campaign_id = lin.campaign_id

            ORDER BY c.campaign_id
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            print("No campaign records found.")
            return

        print("\n========== CAMPAIGN ROI ANALYSIS ==========\n")

        for row in results:
            spend = float(row["total_spend"])

            print("Campaign ID:", row["campaign_id"])
            print("Campaign Name:", row["campaign_name"])
            print("Currency:", row["currency"])
            print("Campaign Spend:", f"{spend:.2f}")

            models = {
                "First Touch": float(row["first_touch_revenue"]),
                "Last Touch": float(row["last_touch_revenue"]),
                "Linear": float(row["linear_revenue"])
            }

            for model_name, revenue in models.items():
                roi = calculate_roi(revenue, spend)

                if roi is None:
                    print(
                        f"{model_name} | Revenue: {revenue:.2f} "
                        "| ROI: N/A (No campaign spend)"
                    )
                else:
                    print(
                        f"{model_name} | Revenue: {revenue:.2f} "
                        f"| ROI: {roi:.2f}%"
                    )

            print("-------------------------------------------")

        print("\nROI analysis completed successfully.")

    except Exception as error:
        print("Error:", error)

    finally:
        cursor.close()
        connection.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
