import os

# Files or folders to entirely skip
EXCLUDE_NAMES = {
    '.git', '__pycache__', '.github', '.env', '.env.example', 
    '.gitignore', 'bundle.py', 'full_codebase.txt'
}

# Only read common text/code extensions to prevent binary corruption
VALID_EXTENSIONS = {
    '.py', '.sql', '.md', '.txt', '.json', '.yml', '.yaml', '.html', '.css'
}

with open('full_codebase.txt', 'w', encoding='utf-8') as outfile:
    for root, dirs, files in os.walk('.'):
        # Filter folders in-place to prevent walking down excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_NAMES]
        
        for file in files:
            if file in EXCLUDE_NAMES:
                continue
                
            file_path = os.path.join(root, file)
            
            # Correctly split the name and extension tuple
            name, ext = os.path.splitext(file)
            
            # Check the lowercased extension string
            if ext.lower() not in VALID_EXTENSIONS:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    # Clear, distinct header formatting for the LLM
                    outfile.write(f"\n\n{'='*80}\n")
                    outfile.write(f"FILE: {file_path}\n")
                    outfile.write(f"{'='*80}\n\n")
                    
                    outfile.write(infile.read())
                print(f"Bundled: {file_path}")
            except Exception as e:
                print(f"Skipped {file_path} due to error: {e}")

print("\nSuccess! All code combined into 'full_codebase.txt'.")