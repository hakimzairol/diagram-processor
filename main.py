import os
import re
import sys
import gemini_client
import db_manager

def get_kumpulan_number(group_name_str: str) -> int:
    """Extracts the integer group number from a string, with a user-input fallback."""
    if group_name_str:
        match = re.search(r'\d+', group_name_str)
        if match:
            return int(match.group(0))
    
    # Fallback to user input
    while True:
        try:
            num = int(input(f"⚠️ Could not auto-detect Kumpulan number from '{group_name_str}'. Please enter the number: ").strip())
            return num
        except (ValueError, TypeError):
            print("❌ Invalid input. Please enter a whole number.")

def assign_categories_interactively(items: list[dict], existing_categories: list[str]) -> list[dict]:
    """Guides the user to assign a category to each item."""
    updated_items = []
    print("\n--- Assign Categories ---")
    if existing_categories:
        print("Previously used categories:", ', '.join(existing_categories))

    for item in items:
        print(f"\nItem: {item['description']}")
        while True:
            category = input("Enter category name: ").strip()
            if category:
                item['category_name'] = category
                updated_items.append(item)
                print(f"✅ Category '{category}' assigned.")
                break
            else:
                print("❌ Category name cannot be empty.")
    return updated_items

def main():
    """Main execution function for the fishbone diagram processor."""
    session_name_input = input("Enter a name for this session (e.g., 'Q1 Marketing 2024'): ").strip()
    if not session_name_input:
        print("❌ Session name cannot be empty. Exiting.")
        sys.exit(1)

    session_schema = db_manager.sanitize_name(session_name_input)
    if not db_manager.setup_session_schema_and_table(session_schema):
        sys.exit(f"❌ Failed to set up database for '{session_schema}'. Exiting.")

    img_path = input("Enter the full path to the image file: ").strip()
    if not os.path.exists(img_path):
        print(f"❌ Image file not found at: {img_path}")
        sys.exit(1)

    print(f"\n⏳ Processing image: {img_path} for session: {session_schema}")
    b64_image = gemini_client.encode_image_to_base64(img_path)
    extracted_info = gemini_client.extract_from_image(b64_image)

    if not extracted_info or 'items' not in extracted_info:
        print("❌ Extraction failed or returned unexpected data. Exiting.")
        print(f"   Received: {extracted_info}")
        sys.exit(1)

    # Process extracted info
    activity_name = extracted_info.get('activity_name', 'DefaultActivity')
    group_name = extracted_info.get('group_name', '')
    kumpulan_no = get_kumpulan_number(group_name)

    print(f"\n--- Extracted Info ---")
    print(f"Activity: {activity_name}")
    print(f"Group: '{group_name}' (using Kumpulan No. {kumpulan_no})")
    
    items_to_process = [
        {'group_no': kumpulan_no, 'description': item['description']}
        for item in extracted_info['items'] if 'description' in item
    ]

    if not items_to_process:
        print("❌ No valid items with descriptions were found in the extraction. Exiting.")
        sys.exit(1)

    # Get user input for categories
    existing_cats = db_manager.fetch_distinct_category_names(session_schema)
    categorized_data = assign_categories_interactively(items_to_process, existing_cats)

    if not categorized_data:
        print("❌ No items were categorized. Exiting.")
        sys.exit(1)

    # Insert data and create views
    records_inserted = db_manager.insert_diagram_data(categorized_data, session_schema, activity_name)
    if records_inserted > 0:
        db_manager.create_category_views(session_schema)
    else:
        print("ℹ️ No records were inserted, so skipping view creation.")

    print(f"\n🎉 Session '{session_name_input}' (schema: '{session_schema}') processing complete.")

if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError) as e:
        # Catch configuration or file errors from config.py
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Process interrupted by user. Exiting.")
        sys.exit(0)