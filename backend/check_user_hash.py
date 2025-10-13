import logging
import sqlite3
from app.core.logging_config import setup_logging
from app.core.security import verify_password

setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

username = 'philornot'
con = sqlite3.connect('tamteklipy.db')
cur = con.cursor()
row = cur.execute("SELECT username, hashed_password FROM users WHERE username=?", (username,)).fetchone()
if not row:
    logger.error('User not found')
else:
    u, h = row
    logger.info(f'User: {u}')
    logger.info(f'Hash prefix: {(h or "")[:7]}')
    try:
        ok_empty = verify_password('', h)
        ok_x = verify_password('x', h)
        logger.info(f'verify("") = {ok_empty}')
        logger.info(f'verify("x") = {ok_x}')
    except Exception as e:
        logger.error(f'verify error: {repr(e)}')
con.close()
