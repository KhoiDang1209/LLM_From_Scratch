import json

try:
    # Load JSON file
    print("Attempting to open JSON file...")
    with open("data_done\\3.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Successfully loaded JSON file")

    # Define output file
    output_file = "violations_clean.txt"

    def clean(text):
        return str(text).replace("\n", " ").replace("\r", " ").strip()

    with open(output_file, "w", encoding="utf-8") as txtfile:
        tables = data.get("tables", [])
        print(f"Found {len(tables)} tables in the JSON data")
        for table in tables:
            rows = table.get("data", [])
            print(f"Processing table with {len(rows)} rows")
            for row in rows:
                cells = row["cells"]
                fields = [
                    clean(cells.get("TT - TT", "")),
                    clean(cells.get("Nội dung vi phạm - Nội dung vi phạm", "")),
                    clean(cells.get("Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Khiển trách", "")),
                    clean(cells.get("Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Cảnh cáo", "")),
                    clean(cells.get("Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Đình chỉ học tập có\nthời hạn", "")),
                    clean(cells.get("Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Buộc thôi học", "")),
                    clean(cells.get("Ghi chú - Ghi chú", "")),
                ]
                # Skip rows that are all empty
                if any(field for field in fields):
                    txtfile.write(" | ".join(fields) + "\n")

    print(f"Plain text conversion completed. Output saved to '{output_file}'")

except FileNotFoundError as e:
    print(f"Error: Could not find the input file: {e}")
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON format in the input file: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")