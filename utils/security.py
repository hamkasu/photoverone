from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# In auth.py routes:
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Prevent brute force
def login():
    # ... existing code