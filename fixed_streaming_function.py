    async def get_ollama_response_with_context_streaming(self, prompt: str, mode: str, context: Dict[str, Any], websocket, client_id: str) -> str:
        """Get streaming response from Ollama LLM enhanced with context"""
        try:
            # Build contextual prompt
            system_prompt = self.get_contextual_system_prompt(mode, context)
            context_info = self.format_context_for_llm(context)
            
            full_prompt = f"{system_prompt}\n\nContext Information:\n{context_info}\n\nUser: {prompt}\nAssistant:"
            
            payload = {
                "model": "llama3.2:1b",  # Fast model for real-time responses
                "prompt": full_prompt,
                "stream": True,  # Enable streaming
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 600
                }
            }
            
            # Send initial acknowledgment
            await websocket.send(json.dumps({
                "type": "chat_response_start",
                "mode": mode,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "🤖 Processing your request..."
            }))
            
            # Stream response using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        full_response = ""
                        chunk_buffer = ""
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if line_text:
                                        chunk_data = json.loads(line_text)
                                        if chunk_data.get("response"):
                                            chunk_text = chunk_data.get("response", "")
                                            full_response += chunk_text
                                            chunk_buffer += chunk_text
                                            
                                            # Send chunks when we have enough content or on word boundaries
                                            if len(chunk_buffer) >= 10 or chunk_text.endswith(' ') or chunk_data.get("done", False):
                                                await websocket.send(json.dumps({
                                                    "type": "chat_response_chunk",
                                                    "mode": mode,
                                                    "chunk": chunk_buffer,
                                                    "client_id": client_id,
                                                    "timestamp": datetime.now().isoformat()
                                                }))
                                                chunk_buffer = ""
                                            
                                            # Check if done
                                            if chunk_data.get("done", False):
                                                break
                                                
                                except json.JSONDecodeError:
                                    continue
                        
                        ai_response = full_response.strip()
                        
                        # Add mode-specific prefix and context indicator
                        mode_prefix = self.get_mode_prefix(mode)
                        confidence = context.get('confidence_score', 0.0)
                        
                        if confidence > 0.6:
                            context_indicator = " [Using high-confidence context]"
                        elif confidence > 0.3:
                            context_indicator = " [Using available context]"
                        else:
                            context_indicator = ""
                        
                        final_response = f"{mode_prefix} {ai_response}{context_indicator}"
                        
                        # Send final completion message
                        await websocket.send(json.dumps({
                            "type": "chat_response_complete",
                            "mode": mode,
                            "full_response": final_response,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat(),
                            "ai_powered": True,
                            "contextual": True
                        }))
                        
                        return final_response
                    else:
                        logger.warning(f"Ollama request failed: {response.status}")
                        fallback_response = await self.get_contextual_fallback_response(prompt, mode, context)
                        
                        # Send fallback response
                        await websocket.send(json.dumps({
                            "type": "chat_response_complete",
                            "mode": mode,
                            "full_response": fallback_response,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat(),
                            "ai_powered": False,
                            "fallback": True
                        }))
                        
                        return fallback_response
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            fallback_response = await self.get_contextual_fallback_response(prompt, mode, context)
            
            # Send error response
            await websocket.send(json.dumps({
                "type": "chat_response_error",
                "mode": mode,
                "error": str(e),
                "fallback_response": fallback_response,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }))
            
            return fallback_response