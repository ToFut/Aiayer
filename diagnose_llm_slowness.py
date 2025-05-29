#!/usr/bin/env python3
"""
LLM Performance Diagnostic Tool
Identifies why LLM responses are slow
"""

import asyncio
import aiohttp
import json
import time
import logging
import psutil
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llm_diagnostic')

class LLMDiagnostic:
    def __init__(self):
        self.ollama_base_url = "http://localhost:11434"
        
    async def test_ollama_api_direct(self):
        """Test direct Ollama API performance"""
        logger.info("🔍 Testing Direct Ollama API Performance...")
        
        try:
            # Test simple generation
            payload = {
                "model": "llama3.2:1b",
                "prompt": "Hello",
                "stream": False
            }
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    elapsed = time.time() - start_time
                    
            logger.info(f"✅ Direct API test completed in {elapsed:.2f}s")
            logger.info(f"   Response: {result.get('response', '')[:50]}...")
            return elapsed
            
        except asyncio.TimeoutError:
            logger.error("❌ Direct API test timed out (30s)")
            return None
        except Exception as e:
            logger.error(f"❌ Direct API test failed: {e}")
            return None
    
    def check_ollama_status(self):
        """Check Ollama service status and resource usage"""
        logger.info("🔍 Checking Ollama Service Status...")
        
        try:
            # Find Ollama processes
            ollama_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                if 'ollama' in proc.info['name'].lower():
                    ollama_processes.append(proc.info)
            
            if not ollama_processes:
                logger.error("❌ No Ollama processes found!")
                return False
                
            logger.info(f"✅ Found {len(ollama_processes)} Ollama processes:")
            for proc in ollama_processes:
                logger.info(f"   PID: {proc['pid']}, CPU: {proc['cpu_percent']:.1f}%, Memory: {proc['memory_percent']:.1f}%")
            
            # Check if any process is using excessive resources
            high_cpu = [p for p in ollama_processes if p['cpu_percent'] > 80]
            if high_cpu:
                logger.warning(f"⚠️  High CPU usage detected: {len(high_cpu)} processes")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to check Ollama status: {e}")
            return False
    
    def check_system_resources(self):
        """Check overall system resource usage"""
        logger.info("🔍 Checking System Resources...")
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            logger.info(f"   CPU Usage: {cpu_percent:.1f}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            logger.info(f"   Memory Usage: {memory.percent:.1f}% ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            logger.info(f"   Disk Usage: {disk.percent:.1f}%")
            
            # Check for resource constraints
            if cpu_percent > 80:
                logger.warning("⚠️  High CPU usage detected!")
            if memory.percent > 85:
                logger.warning("⚠️  High memory usage detected!")
            if disk.percent > 90:
                logger.warning("⚠️  High disk usage detected!")
                
            return {
                'cpu': cpu_percent,
                'memory': memory.percent,
                'disk': disk.percent
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to check system resources: {e}")
            return None
    
    async def test_ollama_models(self):
        """Test which models are available and loaded"""
        logger.info("🔍 Checking Available Models...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get model list
                async with session.get(f"{self.ollama_base_url}/api/tags") as response:
                    models_data = await response.json()
                    
                models = models_data.get('models', [])
                logger.info(f"✅ Found {len(models)} models:")
                
                for model in models:
                    name = model.get('name', 'unknown')
                    size = model.get('size', 0) / (1024**3)  # Convert to GB
                    logger.info(f"   - {name}: {size:.1f}GB")
                    
                # Check if fast model is available
                fast_models = ['llama3.2:1b', 'llama3.2:latest']
                available_fast = [m for m in fast_models if any(m in model['name'] for model in models)]
                
                if available_fast:
                    logger.info(f"✅ Fast models available: {available_fast}")
                else:
                    logger.warning("⚠️  No fast models found!")
                    
                return models
                
        except Exception as e:
            logger.error(f"❌ Failed to check models: {e}")
            return None
    
    def check_llm_service_config(self):
        """Check LLM service configuration"""
        logger.info("🔍 Checking LLM Service Configuration...")
        
        try:
            # Check if llm_service.py exists and read its config
            with open('llm/llm_service.py', 'r') as f:
                content = f.read()
                
            # Look for timeout settings
            if 'timeout' in content:
                logger.info("✅ Timeout settings found in LLM service")
            else:
                logger.warning("⚠️  No timeout settings found")
                
            # Look for model configuration
            if 'llama3.2:1b' in content:
                logger.info("✅ Fast model configured")
            elif 'llama3.2' in content:
                logger.info("⚠️  Using larger model - may be slower")
            else:
                logger.warning("⚠️  Model configuration unclear")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to check LLM service config: {e}")
            return False
    
    async def run_comprehensive_diagnostic(self):
        """Run all diagnostics"""
        logger.info("🚀 Starting LLM Performance Diagnostic")
        logger.info("=" * 60)
        
        results = {}
        
        # 1. System resources
        results['system'] = self.check_system_resources()
        logger.info("")
        
        # 2. Ollama status
        results['ollama_status'] = self.check_ollama_status()
        logger.info("")
        
        # 3. Available models
        results['models'] = await self.test_ollama_models()
        logger.info("")
        
        # 4. LLM service config
        results['llm_config'] = self.check_llm_service_config()
        logger.info("")
        
        # 5. Direct API test
        results['api_test'] = await self.test_ollama_api_direct()
        logger.info("")
        
        # Final recommendations
        logger.info("=" * 60)
        logger.info("📊 DIAGNOSTIC RESULTS & RECOMMENDATIONS")
        logger.info("=" * 60)
        
        # Analyze results
        if results['api_test'] is None:
            logger.error("🚨 CRITICAL: Direct Ollama API is not responding!")
            logger.error("   🔧 Recommendations:")
            logger.error("      1. Restart Ollama: sudo pkill ollama && ollama serve")
            logger.error("      2. Check if port 11434 is blocked")
            logger.error("      3. Try: curl http://localhost:11434/api/version")
            
        elif results['api_test'] > 10:
            logger.warning("⚠️  SLOW: Direct API response is slow")
            logger.warning("   🔧 Recommendations:")
            logger.warning("      1. Use faster model: ollama pull llama3.2:1b")
            logger.warning("      2. Reduce model context size")
            logger.warning("      3. Check system resources")
            
        else:
            logger.info("✅ GOOD: Direct API is responsive")
            logger.info("   🔧 Issue likely in LLM service wrapper or warmup manager")
            
        # System resource recommendations
        system = results.get('system', {})
        if system:
            if system['memory'] > 85:
                logger.warning("   🔧 High memory usage - consider closing other applications")
            if system['cpu'] > 80:
                logger.warning("   🔧 High CPU usage - may affect LLM performance")
        
        # Model recommendations
        models = results.get('models', [])
        if models:
            large_models = [m for m in models if m.get('size', 0) > 5*(1024**3)]  # >5GB
            if large_models:
                logger.info(f"   💡 Consider using smaller model instead of: {[m['name'] for m in large_models]}")
        
        logger.info("=" * 60)
        return results

async def main():
    diagnostic = LLMDiagnostic()
    results = await diagnostic.run_comprehensive_diagnostic()
    
    # Save results
    with open('llm_diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("📄 Diagnostic results saved to: llm_diagnostic_results.json")

if __name__ == "__main__":
    asyncio.run(main())