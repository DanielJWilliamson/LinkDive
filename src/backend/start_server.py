#!/usr/bin/env python3
"""
Link Dive AI server startup script with automatic port clearing.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import structlog
from app.utils.port_manager import clear_port, is_port_available, get_next_available_port
from config.settings import settings

# Configure logging
logger = structlog.get_logger(__name__)


def start_server(port: int = None, clear_ports: bool = True, auto_port: bool = False):
    """Start the Link Dive AI server with port management."""
    
    # Use provided port or default from settings
    target_port = port or settings.port
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Link Dive AI Backend Server")
    logger.info("=" * 60)
    
    if clear_ports:
        logger.info(f"🔍 Checking port {target_port} availability...")
        
        if not is_port_available(target_port):
            logger.info(f"⚠️  Port {target_port} is in use")
            
            if clear_ports:
                logger.info(f"🧹 Clearing port {target_port}...")
                if clear_port(target_port, force=True):
                    logger.info(f"✅ Port {target_port} cleared successfully")
                else:
                    logger.error(f"❌ Failed to clear port {target_port}")
                    
                    if auto_port:
                        logger.info("🔍 Searching for alternative port...")
                        alt_port = get_next_available_port(target_port + 1)
                        if alt_port:
                            logger.info(f"✅ Using alternative port {alt_port}")
                            target_port = alt_port
                        else:
                            logger.error("❌ No alternative ports available")
                            return False
                    else:
                        return False
        else:
            logger.info(f"✅ Port {target_port} is available")
    
    # Start the server
    logger.info(f"🌐 Starting server on http://localhost:{target_port}")
    logger.info("📚 API Documentation: http://localhost:{}/docs".format(target_port))
    logger.info("🔧 Admin Interface: http://localhost:{}/admin".format(target_port))
    
    try:
        import uvicorn
        
        # Update settings port if different
        if target_port != settings.port:
            settings.port = target_port
        
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=target_port,
            reload=settings.debug,
            workers=settings.workers if not settings.debug else 1,
            log_level=settings.log_level.lower(),
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
        return True
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Link Dive AI Backend Server")
    parser.add_argument("--port", "-p", type=int, help=f"Port to run on (default: {settings.port})")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear occupied ports")
    parser.add_argument("--auto-port", action="store_true", help="Automatically find available port if specified port is occupied")
    
    args = parser.parse_args()
    
    success = start_server(
        port=args.port,
        clear_ports=not args.no_clear,
        auto_port=args.auto_port
    )
    
    sys.exit(0 if success else 1)
