"""
Port management utilities for clearing and managing server ports.
"""
import socket
import subprocess
import sys
import time
from typing import List, Optional

import structlog

logger = structlog.get_logger(__name__)


def find_process_using_port(port: int) -> Optional[int]:
    """Find the process ID using the specified port."""
    try:
        if sys.platform == "win32":
            # Windows netstat command
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    # Extract PID from the last column
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            return int(parts[-1])
                        except ValueError:
                            continue
        else:
            # Unix/Linux lsof command
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if result.stdout.strip():
                return int(result.stdout.strip().split('\n')[0])
                
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        pass
    
    return None


def kill_process_on_port(port: int) -> bool:
    """Kill the process using the specified port."""
    pid = find_process_using_port(port)
    
    if pid is None:
        logger.info(f"No process found using port {port}")
        return True
    
    try:
        if sys.platform == "win32":
            # Windows taskkill command
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)], 
                capture_output=True, 
                check=True
            )
        else:
            # Unix/Linux kill command
            subprocess.run(
                ["kill", "-9", str(pid)], 
                capture_output=True, 
                check=True
            )
        
        logger.info(f"Successfully killed process {pid} using port {port}")
        
        # Wait a bit for the port to be released
        time.sleep(1)
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to kill process {pid} on port {port}: {e}")
        return False


def is_port_available(port: int, host: str = "localhost") -> bool:
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, port))
            return True
    except OSError:
        return False


def clear_port(port: int, force: bool = True) -> bool:
    """Clear a port by killing any process using it."""
    logger.info(f"Checking port {port} availability...")
    
    if is_port_available(port):
        logger.info(f"Port {port} is already available")
        return True
    
    if not force:
        logger.warning(f"Port {port} is in use and force=False")
        return False
    
    logger.info(f"Port {port} is in use, attempting to clear...")
    success = kill_process_on_port(port)
    
    if success:
        # Double-check the port is now available
        if is_port_available(port):
            logger.info(f"Port {port} successfully cleared")
            return True
        else:
            logger.error(f"Port {port} still not available after clearing")
            return False
    
    return False


def clear_multiple_ports(ports: List[int], force: bool = True) -> bool:
    """Clear multiple ports."""
    success = True
    
    for port in ports:
        if not clear_port(port, force):
            success = False
            logger.error(f"Failed to clear port {port}")
    
    return success


def get_next_available_port(start_port: int, max_attempts: int = 10) -> Optional[int]:
    """Find the next available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None
