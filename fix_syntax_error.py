#!/usr/bin/env python3

def fix_syntax_error():
    with open('enhanced_enterprise_backend_with_context.py', 'r') as f:
        lines = f.readlines()
    
    # Find and fix the problematic section around line 1744
    fixed_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        # Skip the problematic except block that appears after else
        if 'else:' in line and i + 1 < len(lines) and 'except Exception as e:' in lines[i + 1]:
            fixed_lines.append(line)
            skip_next = True
            continue
        
        if skip_next and 'except Exception as e:' in line:
            skip_next = False
            continue
        
        # Fix indentation for the logger.error line that should be in the except block
        if 'logger.error(f"❌ Error executing plan' in line and 'await websocket.send' in lines[i + 1]:
            # This should be inside the except block, so fix indentation
            fixed_lines.append('                            ' + line.lstrip())
        else:
            fixed_lines.append(line)
    
    with open('enhanced_enterprise_backend_with_context.py', 'w') as f:
        f.writelines(fixed_lines)

if __name__ == "__main__":
    fix_syntax_error()
    print("Fixed syntax error!") 