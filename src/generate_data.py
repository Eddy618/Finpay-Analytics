from faker import Faker
import csv
import os
import random
import uuid
from datetime import datetime, timedelta

fake = Faker("en_NG")

# ============================================
# SETTINGS
# ============================================

NUM_CUSTOMERS = 1000
NUM_MERCHANTS = 200
NUM_TRANSACTIONS = 10000

DATA_FOLDER = "data/raw"

os.makedirs(DATA_FOLDER, exist_ok=True)


# ============================================
# REFERENCE DATA
# ============================================

CITIES = [
    "Lagos",
    "Abuja",
    "Port Harcourt",
    "Ibadan",
    "Kano",
    "Benin City",
    "Enugu",
    "Kaduna"
]

CUSTOMER_TYPES = [
    "Individual",
    "SME",
    "Corporate"
]

BUSINESS_TYPES = [
    "Retail",
    "Restaurant",
    "E-commerce",
    "Logistics",
    "Healthcare",
    "Education",
    "Travel",
    "Entertainment"
]

PAYMENT_CHANNELS = [
    "Card",
    "Bank Transfer",
    "USSD",
    "Mobile Wallet",
    "POS",
    "Direct Debit"
]

PARTNERS = [
    "Flutterwave",
    "Paystack",
    "Interswitch",
    "Moniepoint",
    "OPay",
    "Bank Partner"
]

TRANSACTION_TYPES = [
    "Payment",
    "Transfer",
    "Refund",
    "Withdrawal"
]

TRANSACTION_STATUSES = [
    "Successful",
    "Successful",
    "Successful",
    "Successful",
    "Failed",
    "Pending",
    "Refunded"
]


# ============================================
# GENERATE CUSTOMERS
# ============================================

def generate_customers():

    customers = []
    used_emails = set()

    for customer_id in range(1, NUM_CUSTOMERS + 1):

        # Generate a unique email
        email = fake.email()

        while email in used_emails:
            email = fake.email()

        used_emails.add(email)

        customer = {
            "customer_id": customer_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": email,
            "phone": fake.phone_number(),
            "country": "Nigeria",
            "city": random.choice(CITIES),
            "customer_type": random.choice(CUSTOMER_TYPES),
            "registration_date": fake.date_between(
                start_date="-3y",
                end_date="today"
            )
        }

        customers.append(customer)

    return customers

# ============================================
# GENERATE MERCHANTS
# ============================================

def generate_merchants():

    merchants = []

    for merchant_id in range(1, NUM_MERCHANTS + 1):

        merchant = {
            "merchant_id": merchant_id,
            "merchant_name": fake.company(),
            "business_type": random.choice(BUSINESS_TYPES),
            "country": "Nigeria",
            "city": random.choice(CITIES),
            "registration_date": fake.date_between(
                start_date="-3y",
                end_date="today"
            ),
            "merchant_status": random.choice([
                "Active",
                "Active",
                "Active",
                "Suspended"
            ])
        }

        merchants.append(merchant)

    return merchants


# ============================================
# GENERATE TRANSACTIONS
# ============================================

def generate_transactions():

    transactions = []

    start_date = datetime.now() - timedelta(days=365)

    for _ in range(NUM_TRANSACTIONS):

        transaction_id = str(uuid.uuid4())

        transaction_date = (
            start_date +
            timedelta(
                days=random.randint(0, 364),
                seconds=random.randint(0, 86399)
            )
        )

        transaction_type = random.choice(
            TRANSACTION_TYPES
        )

        transaction_status = random.choice(
            TRANSACTION_STATUSES
        )

        # Most transactions are normal,
        # occasionally create large transactions
        if random.random() < 0.02:

            amount = round(
                random.uniform(500000, 5000000),
                2
            )

        else:

            amount = round(
                random.uniform(500, 250000),
                2
            )

        currency = "NGN"

        customer_id = random.randint(
            1,
            NUM_CUSTOMERS
        )

        merchant_id = random.randint(
            1,
            NUM_MERCHANTS
        )

        channel = random.choice(
            PAYMENT_CHANNELS
        )

        partner = random.choice(
            PARTNERS
        )

        # Successful transactions normally
        # complete within a few minutes
        completed_timestamp = None

        if transaction_status in [
            "Successful",
            "Refunded"
        ]:

            completed_timestamp = (
                transaction_date +
                timedelta(
                    seconds=random.randint(
                        5,
                        600
                    )
                )
            )

        failure_reason = None

        if transaction_status == "Failed":

            failure_reason = random.choice([
                "Insufficient Funds",
                "Network Error",
                "Bank Declined",
                "Invalid Account",
                "Timeout",
                "Fraud Check Failed"
            ])

        transaction = {

            "transaction_id":
                transaction_id,

            "customer_id":
                customer_id,

            "merchant_id":
                merchant_id,

            "channel":
                channel,

            "partner":
                partner,

            "transaction_type":
                transaction_type,

            "transaction_status":
                transaction_status,

            "amount":
                amount,

            "currency":
                currency,

            "transaction_timestamp":
                transaction_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "completed_timestamp":
                (
                    completed_timestamp.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if completed_timestamp
                    else None
                ),

            "failure_reason":
                failure_reason
        }

        transactions.append(transaction)

    return transactions


# ============================================
# SAVE CSV
# ============================================

def save_csv(data, filename):

    if not data:
        return

    filepath = os.path.join(
        DATA_FOLDER,
        filename
    )

    with open(
        filepath,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=data[0].keys()
        )

        writer.writeheader()

        writer.writerows(data)

    print(
        f"Created: {filepath}"
    )

    print(
        f"Records: {len(data)}"
    )


# ============================================
# MAIN
# ============================================

def main():

    print("================================")
    print("   FINPAY DATA GENERATOR")
    print("================================")

    print("\nGenerating customers...")

    customers = generate_customers()

    print("Generating merchants...")

    merchants = generate_merchants()

    print("Generating transactions...")

    transactions = generate_transactions()

    save_csv(
        customers,
        "customers.csv"
    )

    save_csv(
        merchants,
        "merchants.csv"
    )

    save_csv(
        transactions,
        "transactions.csv"
    )

    print("\nData generation complete!")


if __name__ == "__main__":

    main()