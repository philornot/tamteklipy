import sqlite3
from app.core.security import verify_password

username = 'philornot'
con = sqlite3.connect('tamteklipy.db')
cur = con.cursor()
row = cur.execute("SELECT username, hashed_password FROM users WHERE username=?", (username,)).fetchone()
if not row:
    print('User not found')
else:
    u, h = row
    print('User:', u)
    print('Hash prefix:', (h or '')[:7])
    try:
        ok_empty = verify_password('', h)
        ok_x = verify_password('x', h)
        print('verify("") =', ok_empty)
        print('verify("x") =', ok_x)
    except Exception as e:
        print('verify error:', repr(e))
con.close()

