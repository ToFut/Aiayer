#!/usr/bin/env python3

def fix_all_indentation():
    with open('enhanced_enterprise_backend_with_context.py', 'r') as f:
        content = f.read()
    
    # Fix specific indentation issues
    fixes = [
        # Fix line 1578
        ('                        except Exception as e:', '                        except Exception as e:'),
        # Fix line 1580
        ('                            await websocket.send(json.dumps({', '                            await websocket.send(json.dumps({'),
        # Fix line 1581
        ('                                "type": "error",', '                                "type": "error",'),
        # Fix line 1582
        ('                                "error": f"Error processing chat request: {str(e)}",', '                                "error": f"Error processing chat request: {str(e)}",'),
        # Fix line 1583
        ('                                "client_id": client_id,', '                                "client_id": client_id,'),
        # Fix line 1584
        ('                                "session_id": session_id,', '                                "session_id": session_id,'),
        # Fix line 1585
        ('                                "timestamp": datetime.now().isoformat(),', '                                "timestamp": datetime.now().isoformat(),'),
        # Fix line 1586
        ('                                "success": False', '                                "success": False'),
        # Fix line 1587
        ('                            }))', '                            }))'),
        # Fix line 1720
        ('                                    await websocket.send(json.dumps({', '                            await websocket.send(json.dumps({'),
        # Fix line 1725
        ('                                    else:', '                            else:'),
        # Fix line 1727
        ('                            except Exception as e:', '                            except Exception as e:'),
        # Fix line 1747
        ('                                    await websocket.send(json.dumps({', '                            await websocket.send(json.dumps({'),
        # Fix line 1748
        ('                                "type": "execution_completed",', '                                "type": "execution_completed",'),
        # Fix line 1749
        ('                                        "plan_id": plan_id,', '                                "plan_id": plan_id,'),
        # Fix line 1750
        ('                                "client_id": client_id,', '                                "client_id": client_id,'),
        # Fix line 1751
        ('                                "session_id": session_id,', '                                "session_id": session_id,'),
        # Fix line 1752
        ('                                        "timestamp": datetime.now().isoformat(),', '                                "timestamp": datetime.now().isoformat(),'),
        # Fix line 1753
        ('                                "success": execution_result.get("success", False),', '                                "success": execution_result.get("success", False),'),
        # Fix line 1754
        ('                                "steps_completed": execution_result.get("steps_completed", 0),', '                                "steps_completed": execution_result.get("steps_completed", 0),'),
        # Fix line 1755
        ('                                "steps_failed": execution_result.get("steps_failed", 0),', '                                "steps_failed": execution_result.get("steps_failed", 0),'),
        # Fix line 1756
        ('                                "total_steps": execution_result.get("total_steps", 0),', '                                "total_steps": execution_result.get("total_steps", 0),'),
        # Fix line 1757
        ('                                "success_rate": execution_result.get("success_rate", 0),', '                                "success_rate": execution_result.get("success_rate", 0),'),
        # Fix line 1758
        ('                                "total_execution_time": execution_result.get("total_execution_time", 0),', '                                "total_execution_time": execution_result.get("total_execution_time", 0),'),
        # Fix line 1759
        ('                                "summary": execution_result.get("summary", ""),', '                                "summary": execution_result.get("summary", ""),'),
        # Fix line 1760
        ('                                "detailed_reasoning": execution_result.get("detailed_reasoning", ""),', '                                "detailed_reasoning": execution_result.get("detailed_reasoning", ""),'),
        # Fix line 1761
        ('                                "execution_results": execution_result.get("execution_results", [])', '                                "execution_results": execution_result.get("execution_results", [])'),
        # Fix line 1762
        ('                            }))', '                            }))'),
        # Fix line 1765
        ('                                    else:', '                            else:'),
        # Fix line 1767
        ('                            except Exception as e:', '                            except Exception as e:'),
        # Fix line 1768
        ('                            logger.error(f"❌ Error executing plan {plan_id}: {e}")', '                            logger.error(f"❌ Error executing plan {plan_id}: {e}")'),
        # Fix line 1769
        ('                                await websocket.send(json.dumps({', '                                await websocket.send(json.dumps({'),
        # Fix line 1770
        ('                                    "type": "execution_error",', '                                    "type": "execution_error",'),
        # Fix line 1771
        ('                                "error": f"Plan execution failed: {str(e)}",', '                                "error": f"Plan execution failed: {str(e)}",'),
        # Fix line 1772
        ('                            "plan_id": plan_id,', '                                "plan_id": plan_id,'),
        # Fix line 1773
        ('                            "client_id": client_id,', '                                "client_id": client_id,'),
        # Fix line 1774
        ('                            "session_id": session_id,', '                                "session_id": session_id,'),
        # Fix line 1775
        ('                            "timestamp": datetime.now().isoformat(),', '                                "timestamp": datetime.now().isoformat(),'),
        # Fix line 1776
        ('                                "success": False', '                                "success": False'),
        # Fix line 1777
        ('                        }))', '                            }))'),
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    with open('enhanced_enterprise_backend_with_context.py', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_all_indentation()
    print("Fixed all indentation issues!") 