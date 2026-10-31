
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta, time

# Add project root before importing backend modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_connection


# Fixed seed and reference date
SEED = 20261022
random.seed(SEED)

AS_OF = datetime(2026, 10, 31, 23, 59, 59)


def generate_journeys():

    connection = get_connection()

    if connection is None:
        print("MySQL connection failed.")
        return

    cursor = connection.cursor()

    try:
        # Prevent duplicate generation
        for table in [
            "web_sessions",
            "touchpoints",
            "leads",
            "opportunities"
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")

            if cursor.fetchone()[0] > 0:
                print(f"{table} already contains data. Stopping.")
                return

        # Fetch contacts
        cursor.execute("""
            SELECT contact_id, created_at
            FROM contacts
        """)
        contacts = cursor.fetchall()

        # Fetch eligible campaign, channel and creative combinations
        cursor.execute("""
            SELECT
                c.campaign_id,
                cc.channel_id,
                cr.creative_id,
                ch.channel_name,
                c.start_date,
                c.end_date
            FROM campaigns c
            JOIN campaign_channels cc
                ON c.campaign_id = cc.campaign_id
            JOIN channels ch
                ON cc.channel_id = ch.channel_id
            JOIN creatives cr
                ON c.campaign_id = cr.campaign_id
        """)
        campaign_options = cursor.fetchall()

        sessions = []
        touchpoints = []
        contact_journeys = {}

        session_number = 1
        touch_numbers = {}

        # Generate website sessions and touchpoints
        for contact_id, contact_created in contacts:

            eligible_campaigns = []

            for campaign in campaign_options:

                campaign_id, channel_id, creative_id, channel_name, start_date, end_date = campaign

                lower = max(
                    contact_created,
                    datetime.combine(start_date, time.min)
                )

                upper = min(
                    datetime.combine(end_date, time.max),
                    AS_OF - timedelta(minutes=30)
                )

                if lower <= upper:
                    eligible_campaigns.append(campaign)

            if not eligible_campaigns:
                continue

            number_of_touches = random.randint(1, 3)

            contact_journeys[contact_id] = []

            for _ in range(number_of_touches):

                campaign = random.choice(eligible_campaigns)

                (
                    campaign_id,
                    channel_id,
                    creative_id,
                    channel_name,
                    start_date,
                    end_date
                ) = campaign

                lower = max(
                    contact_created,
                    datetime.combine(start_date, time.min)
                )

                upper = min(
                    datetime.combine(end_date, time.max),
                    AS_OF - timedelta(minutes=30)
                )

                seconds = int((upper - lower).total_seconds())

                touch_time = lower + timedelta(
                    seconds=random.randint(0, seconds)
                )

                session_id = f"SES-2026-{session_number:06d}"

                touch_numbers[contact_id] = (
                    touch_numbers.get(contact_id, 0) + 1
                )

                touchpoint_id = (
                    f"TOUCH-{contact_id}-"
                    f"{touch_numbers[contact_id]:06d}"
                )

                session_start = max(
                    contact_created,
                    touch_time - timedelta(
                        minutes=random.randint(1, 10)
                    )
                )

                session_end = touch_time + timedelta(
                    minutes=random.randint(5, 30)
                )

                # Store website session
                sessions.append((
                    session_id,
                    contact_id,
                    None,
                    session_start,
                    session_end,
                    "/landing"
                ))

                # Store marketing interaction
                touchpoints.append((
                    touchpoint_id,
                    contact_id,
                    campaign_id,
                    channel_id,
                    creative_id,
                    session_id,
                    random.choice([
                        "Ad Click",
                        "Email Open",
                        "Email Click",
                        "Website Visit",
                        "Social Engagement",
                        "Referral Visit"
                    ]),
                    touch_time,
                    channel_name
                ))

                contact_journeys[contact_id].append({
                    "touchpoint_id": touchpoint_id,
                    "campaign_id": campaign_id,
                    "session_id": session_id,
                    "touch_time": touch_time
                })

                session_number += 1

        # Insert sessions first because touchpoints reference them
        cursor.executemany("""
            INSERT INTO web_sessions
            (session_id, contact_id, anonymous_id,
             started_at, ended_at, landing_page)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, sessions)

        # Insert touchpoints
        cursor.executemany("""
            INSERT INTO touchpoints
            (touchpoint_id, contact_id, campaign_id,
             channel_id, creative_id, session_id,
             touchpoint_type, touchpoint_time, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, touchpoints)

        # Generate leads from contacts with interactions
        eligible_contacts = list(contact_journeys.keys())

        selected_contacts = random.sample(
            eligible_contacts,
            min(35, len(eligible_contacts))
        )

        leads = []
        lead_details = []

        for i, contact_id in enumerate(selected_contacts, start=1):

            source_touch = random.choice(
                contact_journeys[contact_id]
            )

            lead_id = f"LEAD-2026-{i:06d}"

            lead_created = min(
                AS_OF,
                source_touch["touch_time"] + timedelta(
                    days=random.randint(1, 14)
                )
            )

            lead_status = random.choice([
                "New",
                "Contacted",
                "Qualified",
                "Disqualified",
                "Converted"
            ])

            leads.append((
                lead_id,
                contact_id,
                source_touch["campaign_id"],
                source_touch["touchpoint_id"],
                source_touch["session_id"],
                lead_status,
                lead_created
            ))

            lead_details.append({
                "lead_id": lead_id,
                "created_at": lead_created
            })

        cursor.executemany("""
            INSERT INTO leads
            (lead_id, contact_id, campaign_id,
             source_touchpoint_id, session_id,
             lead_status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, leads)

        # Generate sales opportunities
        selected_leads = random.sample(
            lead_details,
            min(20, len(lead_details))
        )

        opportunities = []

        for i, lead in enumerate(selected_leads, start=1):

            opportunity_id = f"OPP-2026-{i:06d}"

            opportunity_created = min(
                AS_OF,
                lead["created_at"] + timedelta(
                    days=random.randint(1, 10)
                )
            )

            stage = random.choice([
                "Prospect",
                "Qualified",
                "Proposal",
                "Negotiation",
                "Closed Won",
                "Closed Lost"
            ])

            closed_at = None

            if stage in ["Closed Won", "Closed Lost"]:

                possible_close_date = (
                    opportunity_created + timedelta(
                        days=random.randint(1, 20)
                    )
                )

                if possible_close_date <= AS_OF:
                    closed_at = possible_close_date
                else:
                    stage = "Negotiation"

            opportunities.append((
                opportunity_id,
                lead["lead_id"],
                f"Sales Opportunity {i}",
                round(random.uniform(5000, 100000), 2),
                "INR",
                stage,
                opportunity_created,
                closed_at
            ))

        cursor.executemany("""
            INSERT INTO opportunities
            (opportunity_id, lead_id, opportunity_name,
             amount, currency, stage, created_at, closed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, opportunities)

        connection.commit()

        print("\nCustomer journey data generated successfully!")
        print("Website sessions:", len(sessions))
        print("Touchpoints:", len(touchpoints))
        print("Leads:", len(leads))
        print("Opportunities:", len(opportunities))

    except Exception as error:
        connection.rollback()
        print("Data generation failed:", error)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_journeys()
