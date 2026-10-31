from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import get_connection

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)

CORS(app)


@app.route("/")
def home():
    return send_from_directory("../frontend", "index.html")


@app.route("/api/summary")
def summary():
    connection = get_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                COALESCE(SUM(amount), 0) AS total_spend
            FROM cost_records
        """)
        spend = float(cursor.fetchone()["total_spend"])

        cursor.execute("""
            SELECT
                COALESCE(SUM(revenue), 0) AS total_revenue
            FROM orders
            WHERE order_status = 'Completed'
        """)
        revenue = float(cursor.fetchone()["total_revenue"])

        roi = (
            ((revenue - spend) / spend) * 100
            if spend > 0 else None
        )

        return jsonify({
            "total_spend": round(spend, 2),
            "total_revenue": round(revenue, 2),
            "overall_roi": round(roi, 2) if roi is not None else None
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/campaigns")
def campaigns():
    connection = get_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                c.campaign_id,
                c.campaign_name,
                c.currency,
                COALESCE(s.total_spend, 0) AS total_spend,
                COALESCE(f.revenue, 0) AS first_touch_revenue,
                COALESCE(l.revenue, 0) AS last_touch_revenue,
                COALESCE(n.revenue, 0) AS linear_revenue

            FROM campaigns c

            LEFT JOIN (
                SELECT campaign_id, SUM(amount) AS total_spend
                FROM cost_records
                GROUP BY campaign_id
            ) s ON c.campaign_id = s.campaign_id

            LEFT JOIN (
                SELECT campaign_id, SUM(attributed_revenue) AS revenue
                FROM attribution_results
                WHERE attribution_model = 'First Touch'
                GROUP BY campaign_id
            ) f ON c.campaign_id = f.campaign_id

            LEFT JOIN (
                SELECT campaign_id, SUM(attributed_revenue) AS revenue
                FROM attribution_results
                WHERE attribution_model = 'Last Touch'
                GROUP BY campaign_id
            ) l ON c.campaign_id = l.campaign_id

            LEFT JOIN (
                SELECT campaign_id, SUM(attributed_revenue) AS revenue
                FROM attribution_results
                WHERE attribution_model = 'Linear'
                GROUP BY campaign_id
            ) n ON c.campaign_id = n.campaign_id

            ORDER BY c.campaign_id
        """)

        rows = cursor.fetchall()

        for row in rows:
            spend = float(row["total_spend"])

            for model in [
                "first_touch",
                "last_touch",
                "linear"
            ]:
                revenue = float(row[f"{model}_revenue"])

                row[f"{model}_roi"] = (
                    round(((revenue - spend) / spend) * 100, 2)
                    if spend > 0 else None
                )

            for key in [
                "total_spend",
                "first_touch_revenue",
                "last_touch_revenue",
                "linear_revenue"
            ]:
                row[key] = round(float(row[key]), 2)

        return jsonify(rows)

    except Exception as error:
        return jsonify({"error": str(error)}), 500

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
