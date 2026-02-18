
import argparse
import sys
import os

# Ensure advisor_ai is in path
sys.path.append(os.getcwd())

from advisor_ai.elective_service import ElectiveService

def main():
    parser = argparse.ArgumentParser(description="Admin Tool for Elective Service")
    parser.add_argument("--file", help="Path to Excel/PDF/Image file")
    parser.add_argument("--text", help="Raw text input (comma separated or newlines)")
    parser.add_argument("--term", help="Set active term (e.g., 'Spring-2026')")
    
    args = parser.parse_args()
    service = ElectiveService()

    if args.term:
        service.set_term(args.term)
        print(f"Active term set to: {args.term}")

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            return
        print(f"Uploading from file: {args.file}...")
        results = service.upload(args.file)
        print(f"Uploaded {len(results)} electives.")
        
    if args.text:
        print("Uploading from text input...")
        results = service.upload(args.text)
        print(f"Uploaded {len(results)} electives.")

    if not any([args.file, args.text, args.term]):
        parser.print_help()

if __name__ == "__main__":
    main()
