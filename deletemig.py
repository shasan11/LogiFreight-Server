import os


def delete_migration_files_except_init():
    # Get the base directory (where manage.py is located)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Loop through each item in the base directory
    for root, dirs, files in os.walk(base_dir):
        # Look for a 'migrations' folder
        if 'migrations' in dirs:
            migrations_folder = os.path.join(root, 'migrations')
            
            # Loop through files in the migrations folder
            for filename in os.listdir(migrations_folder):
                file_path = os.path.join(migrations_folder, filename)
                
                # Delete the file if it's not __init__.py and is a file (not a directory)
                if filename != "__init__.py" and os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")

            print(f"Processed migrations folder: {migrations_folder}")

# Run the function
delete_migration_files_except_init()