#!/usr/bin/env python3
"""
Generate a CSV dataset with 5 columns and 5M rows for OLAP/column store experiments.

Columns:
- id: Unique identifier (1 to 5,000,000)
- name: Random name (e.g., "Alice", "Bob", ...)
- type: Transaction type (A, B, C, D, E) - for filtering
- amount: Random amount (10.00 to 10000.00) - for aggregation
- date: Random date in 2024 - for time-based queries
"""

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path


def generate_name() -> str:
    """Generate a random name."""
    first_names = [
        "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry",
        "Ivy", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Paul",
        "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier",
        "Yara", "Zoe"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
        "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_date() -> str:
    """Generate a random date in 2024."""
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)
    random_date = start + timedelta(
        days=random.randint(0, (end - start).days)
    )
    return random_date.strftime("%Y-%m-%d")


def generate_dataset(output_file: str, num_rows: int = 5_000_000):
    """
    Generate CSV dataset with 5 columns and specified number of rows.
    
    Args:
        output_file: Path to output CSV file
        num_rows: Number of rows to generate (default: 5,000,000)
    """
    print(f"Generating dataset: {num_rows:,} rows → {output_file}")
    print("This may take a few minutes...")
    
    # Types distribution (for realistic filtering)
    types = ["A", "B", "C", "D", "E"]
    type_weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Type A is most common
    
    start_time = datetime.now()
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["id", "name", "type", "amount", "date"])
        
        # Write rows
        for i in range(1, num_rows + 1):
            # Generate row data
            row_id = i
            name = generate_name()
            transaction_type = random.choices(types, weights=type_weights)[0]
            amount = round(random.uniform(10.0, 10000.0), 2)
            date = generate_date()
            
            writer.writerow([row_id, name, transaction_type, amount, date])
            
            # Progress indicator
            if i % 500_000 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (num_rows - i) / rate if rate > 0 else 0
                print(
                    f"  Progress: {i:,}/{num_rows:,} rows "
                    f"({i*100//num_rows}%) - "
                    f"ETA: {remaining:.0f}s"
                )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    file_size = Path(output_file).stat().st_size / (1024 * 1024)  # MB
    
    print(f"\n✅ Dataset generated successfully!")
    print(f"   Rows: {num_rows:,}")
    print(f"   File: {output_file}")
    print(f"   Size: {file_size:.2f} MB")
    print(f"   Time: {elapsed:.2f} seconds")
    print(f"   Rate: {num_rows/elapsed:,.0f} rows/second")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        num_rows = int(sys.argv[1])
    else:
        num_rows = 5_000_000
    
    output_file = "dataset_5m.csv"
    
    if Path(output_file).exists():
        response = input(
            f"File {output_file} already exists. Overwrite? (y/n): "
        )
        if response.lower() != "y":
            print("Cancelled.")
            return
    
    generate_dataset(output_file, num_rows)


if __name__ == "__main__":
    main()
