#!/usr/bin/env python3
"""
Quick fix for indentation issue in ultimate_do_button_server.py
"""
import os
import sys

def fix_indentation():
    with open('enhanced_enterprise_backend_with_context.py', 'r') as f:
        lines = f.readlines()
    
    # Fix specific indentation issues
    fixed_lines = []
    for i, line in enumerate(lines):
        # Fix line 1578 (around line 1578)
        if i == 1577 and 'except Exception as e:' in line:
            fixed_lines.append('                        except Exception as e:\n')
        # Fix line 1580
        elif i == 1579 and 'await websocket.send' in line:
            fixed_lines.append('                            await websocket.send(json.dumps({\n')
        # Fix line 1581
        elif i == 1580 and '"type": "error"' in line:
            fixed_lines.append('                                "type": "error",\n')
        # Fix line 1582
        elif i == 1581 and '"error":' in line:
            fixed_lines.append('                                "error": f"Error processing chat request: {str(e)}",\n')
        # Fix line 1583
        elif i == 1582 and '"client_id":' in line:
            fixed_lines.append('                                "client_id": client_id,\n')
        # Fix line 1584
        elif i == 1583 and '"session_id":' in line:
            fixed_lines.append('                                "session_id": session_id,\n')
        # Fix line 1585
        elif i == 1584 and '"timestamp":' in line:
            fixed_lines.append('                                "timestamp": datetime.now().isoformat(),\n')
        # Fix line 1586
        elif i == 1585 and '"success": False' in line:
            fixed_lines.append('                                "success": False\n')
        # Fix line 1587
        elif i == 1586 and '}))' in line:
            fixed_lines.append('                            }))\n')
        # Fix line 1720
        elif i == 1719 and 'await websocket.send' in line:
            fixed_lines.append('                            await websocket.send(json.dumps({\n')
        # Fix line 1725
        elif i == 1724 and 'else:' in line:
            fixed_lines.append('                            else:\n')
        # Fix line 1727
        elif i == 1726 and 'except Exception as e:' in line:
            fixed_lines.append('                            except Exception as e:\n')
        else:
            fixed_lines.append(line)
    
    with open('enhanced_enterprise_backend_with_context.py', 'w') as f:
        f.writelines(fixed_lines)

if __name__ == "__main__":
    fix_indentation()
    print("Fixed indentation issues!")