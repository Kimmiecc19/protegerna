import os
import shutil
import argparse

def unpack_files(main_dir):
    # Traverse the directory
    for subdir, _, files in os.walk(main_dir):
        for file in files:
            # Create full path to the file
            file_path = os.path.join(subdir, file)
            # Move file to the main directory
            shutil.move(file_path, main_dir)
    
    # Remove empty subdirectories
    for subdir, dirs, _ in os.walk(main_dir, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(subdir, dir)
            try:
                os.rmdir(dir_path)
            except OSError:
                # Directory is not empty
                pass

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Unpack files from subdirectories into a main directory.")
    parser.add_argument("main_directory", type=str, help="Path to the main directory containing subdirectories.")

    # Parse arguments
    args = parser.parse_args()

    # Call the unpack function with the provided directory
    unpack_files(args.main_directory)
