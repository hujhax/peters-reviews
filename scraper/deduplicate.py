import csv

def deduplicate(input_file, output_file):
    print(f"Deduplicating {input_file}...")
    seen = set()
    unique_records = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                # Use title, link, and post_date as the unique identifier
                identifier = (row['title'], row['link'], row['post_date'])
                if identifier not in seen:
                    seen.add(identifier)
                    unique_records.append(row)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(unique_records)
            
        print(f"Successfully deduplicated. Records reduced from {len(seen) + (28114 - len(seen))} to {len(unique_records)}.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deduplicate('scraper/peter_reviews_data.csv', 'scraper/peter_reviews_data_clean.csv')
