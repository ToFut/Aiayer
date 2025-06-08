#\!/usr/bin/env python3
import os
import sys
import re

def escape_quotes_in_heredoc(input_file, output_file):
    """Fix quotes in HEREDOC sections of the script"""
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Find HEREDOC sections
    heredoc_sections = re.finditer(r'cat > .*? << [\'"]([A-Z_]+)[\'"](.+?)\1', content, re.DOTALL)
    
    # Process each HEREDOC section
    processed_content = content
    for match in heredoc_sections:
        heredoc_name = match.group(1)
        heredoc_content = match.group(2)
        
        # Replace problematic f-strings containing single quotes with escaped versions
        fixed_content = re.sub(r"f\"([^\"]*)'([^\"]*)'([^\"]*)\"", r'f"\1\\\\"\2\\\\"\3"', heredoc_content)
        fixed_content = re.sub(r"'([^']*)'", r"\\'\1\\'", fixed_content)
        
        # Replace the original section with fixed content
        processed_content = processed_content.replace(match.group(0), 
                                               f'cat > .*? << \'{heredoc_name}\'{fixed_content}{heredoc_name}')
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(processed_content)

# Create a simplified fix for the immediate issue
def simple_fix(input_file, output_file):
    """Create a simplified version without the problematic quotes"""
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Replace the problematic line
    content = content.replace('"message": f"Action \'{action}\' processed (mock implementation)",', 
                             '"message": "Action processed (mock implementation)",')
    
    with open(output_file, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    # Make a backup
    os.system('cp START_MASTER_SYSTEM.sh START_MASTER_SYSTEM.sh.bak')
    
    # Apply simple fix
    simple_fix('START_MASTER_SYSTEM.sh', 'START_MASTER_SYSTEM.sh.fixed')
    
    # Replace original with fixed version
    os.system('mv START_MASTER_SYSTEM.sh.fixed START_MASTER_SYSTEM.sh')
    os.system('chmod +x START_MASTER_SYSTEM.sh')
    
    print("Fixed START_MASTER_SYSTEM.sh")
