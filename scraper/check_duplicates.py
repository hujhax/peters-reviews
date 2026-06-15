import csv
from collections import Counter

def check_duplicates(file_path):
    print(f"Analyzing {file_path} for duplicates...")
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create a tuple of unique identifiers
                # title, link, and post_date should uniquely identify a review
                identifier = (row['title'], row['link'], row['post_date'])
                records.append(identifier)
        
        total_count = len(records)
        counts = Counter(records)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        
        print(f"Total records: {total_count}")
        print(f"Unique records: {len(counts)}")
        print(f"Duplicate records found: {sum(duplicates.values()) - len(duplicates)}")
        
        if duplicates:
            print("\nExample duplicates:")
            for i, (k, v) in enumerate(duplicates.items()):
                if i >= 5: break
                print(f"- {k}: {v} occurrences")
        else:
            print("No duplicates found!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_duplicates('scraper/peter_reviews_data.csv')
