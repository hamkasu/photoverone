"""
PhotoVault utilities package
"""

from functools import wraps
import time
import logging
import random
from sqlalchemy.exc import OperationalError, DisconnectionError, InvalidRequestError
from photovault.extensions import db

class TransientDBError(Exception):
    """Exception raised when database operations fail due to transient issues"""
    pass

def retry_db_operation(max_retries=3, delay=1, backoff=2):
    """
    Decorator to retry database operations on connection failures with proper session handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            engine_disposed = False
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError, InvalidRequestError) as e:
                    error_str = str(e)
                    is_connection_error = (
                        'SSL connection has been closed unexpectedly' in error_str or
                        'connection invalidated' in error_str or
                        'server closed the connection unexpectedly' in error_str or
                        getattr(e, 'connection_invalidated', False)
                    )
                    
                    if is_connection_error:
                        retries += 1
                        if retries >= max_retries:
                            logging.error(f"Database operation failed after {max_retries} retries: {e}")
                            raise TransientDBError(f"Database connection issue after {max_retries} retries") from e
                        
                        # Clean up the session before retry
                        try:
                            db.session.rollback()
                            db.session.close()
                        except Exception:
                            pass  # Session might already be in bad state
                        
                        # Only dispose engine after multiple failures or repeated invalidations
                        if retries >= 2 and not engine_disposed:
                            db.engine.dispose()
                            engine_disposed = True
                        
                        # Exponential backoff with jitter
                        base_wait = delay * (backoff ** (retries - 1))
                        jitter = random.uniform(0.1, 0.3) * base_wait
                        wait_time = base_wait + jitter
                        
                        logging.warning(f"Database connection error, retrying in {wait_time:.2f}s (attempt {retries}/{max_retries}): {e}")
                        time.sleep(wait_time)
                    else:
                        # Non-transient error, don't retry
                        raise e
                except Exception as e:
                    # Non-database error, don't retry
                    raise e
            return None
        return wrapper
    return decorator

def safe_db_query(query_func, operation_name="database query"):
    """
    Execute database query with retry logic, raising TransientDBError on failure
    """
    @retry_db_operation(max_retries=3)
    def execute_query():
        return query_func()
    
    try:
        return execute_query()
    except TransientDBError:
        # Re-raise TransientDBError for proper handling upstream
        raise
    except Exception as e:
        logging.error(f"Database {operation_name} failed: {e}")
        raise