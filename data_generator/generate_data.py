
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta

from faker import Faker

# Make the project root available for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.database import get_connection

# Fixed seed for reproducible data
SEED = 20261022
random.seed(SEED)
fake = Faker("en_IN")
Faker.seed(SEED)

# Small test dataset
NUM_CAMPAIGNS = 10
NUM_CONTACTS = 100

channels = [
    ("CH-001", "Email"),
    ("CH-002", "Google Ads"),
    ("CH-003", "Social Media"),
    ("CH-004", "SEO"),
    ("CH-005", "Referral")
]

audiences = [
    ("AUD-001", "Students", "College and university students"),
    ("AUD-002", "Professionals", "Working professionals"),
    ("AUD-003", "Small Businesses", "Small business owners")
]


def generate_data():
    connection = get_connection()

    if connection is None:
        print("Unable to connect to MySQL.")
        return

    cursor = connection.cursor()

    try:
        # Prevent accidental duplicate insertion
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        if cursor.fetchone()[0] > 0:
            print("Campaign data already exists. Stopping to avoid duplicates.")
            return

        cursor.execute("SELECT COUNT(*) FROM contacts")
        if cursor.fetchone()[0] > 0:
            print("Contact data already exists. Stopping to avoid duplicates.")
            return

        # Insert channels
        cursor.executemany(
            "INSERT INTO channels VALUES (%s, %s)",
            channels
        )

        # Insert audiences
        cursor.executemany(
            "INSERT INTO audiences VALUES (%s, %s, %s)",
            audiences
        )

        # Generate campaigns
        campaign_records = []
        campaign_channel_records = []
        creative_records = []

        for i in range(1, NUM_CAMPAIGNS + 1):
            campaign_id = f"CMP-2026-{i:06d}"
            start_date = fake.date_between(
                start_date="-1y",
                end_date="today"
            )
            end_date = start_date + timedelta(days=random.randint(30, 120))

            campaign_records.append((
                campaign_id,
                f"{fake.catch_phrase()} Campaign",
                random.choice([
                    "Brand Awareness",
                    "Lead Generation",
                    "Sales"
                ]),
                round(random.uniform(10000, 100000), 2),
                "INR",
                start_date,
                end_date,
                random.choice(["Planned", "Active", "Paused", "Completed"])
            ))

            selected_channels = random.sample(
                channels,
                random.randint(1, 3)
            )

            for channel in selected_channels:
                campaign_channel_records.append(
                    (campaign_id, channel[0])
                )

            creative_records.append((
                f"CRE-2026-{i:06d}",
                campaign_id,
                f"Creative {i}",
                random.choice(["Image", "Video", "Text"])
            ))

        cursor.executemany("""
            INSERT INTO campaigns
            (campaign_id, campaign_name, objective, budget,
             currency, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, campaign_records)

        cursor.executemany("""
            INSERT INTO campaign_channels
            (campaign_id, channel_id)
            VALUES (%s, %s)
        """, campaign_channel_records)

        cursor.executemany("""
            INSERT INTO creatives
            (creative_id, campaign_id, creative_name, creative_type)
            VALUES (%s, %s, %s, %s)
        """, creative_records)

        # Generate contacts
        contact_records = []

        for i in range(1, NUM_CONTACTS + 1):
            contact_records.append((
                f"CONT-2026-{i:06d}",
                fake.first_name(),
                fake.last_name(),
                fake.unique.email(),
                fake.date_time_between(
                    start_date="-1y",
                    end_date="now"
                )
            ))

        cursor.executemany("""
            INSERT INTO contacts
            (contact_id, first_name, last_name, email, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, contact_records)

        connection.commit()

        print("Master data generated successfully!")
        print("Channels:", len(channels))
        print("Audiences:", len(audiences))
        print("Campaigns:", len(campaign_records))
        print("Campaign-channel links:", len(campaign_channel_records))
        print("Creatives:", len(creative_records))
        print("Contacts:", len(contact_records))

    except Exception as error:
        connection.rollback()
        print("Data generation failed:", error)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_data()
