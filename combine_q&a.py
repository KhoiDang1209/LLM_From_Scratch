import json
import os
import glob

# Get all JSON files in the qa_json directory
json_files = glob.glob('qa_json/*.json')
print(f"Found {len(json_files)} JSON files")

# Combined dataset
combined_data = []

# Read and combine each JSON file
for file_path in json_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                combined_data.extend(data)
            else:
                combined_data.append(data)
        print(f"Processed: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Save the combined dataset to the current directory
output_path = 'combined_qa_dataset.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=2)

print(f"Combined dataset saved to {output_path}")
print(f"Total entries: {len(combined_data)}")