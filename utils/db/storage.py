
import sqlite3 as lite

class DatabaseManager(object):

    def __init__(self, path):
        self.conn = lite.connect(path)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def create_tables(self):
        self.query('CREATE TABLE IF NOT EXISTS products (idx text, title text, body text, photo blob, price int, tag text)')
        self.query('CREATE TABLE IF NOT EXISTS orders (cid int, usr_name text, usr_address text, products text)')
        self.query('CREATE TABLE IF NOT EXISTS cart (cid int, idx text, quantity int, title text)')
        self.query('CREATE TABLE IF NOT EXISTS categories (idx text, title text)')
        self.query('CREATE TABLE IF NOT EXISTS wallet (cid int, balance real)')
        self.query('CREATE TABLE IF NOT EXISTS questions (cid int, question text)')
        self.query('CREATE TABLE IF NOT EXISTS messages (cid int, username text, message text, message_time int)')
        self.query('CREATE TABLE IF NOT EXISTS open_orders (cid int, username text, order_time int)')
        self.query('CREATE TABLE IF NOT EXISTS closed_orders (cid int, username text, order_time int)')
        self.query('CREATE TABLE IF NOT EXISTS all_users (cid int)')
        self.query('CREATE TABLE IF NOT EXISTS blocked_users (cid int)')
        self.query('CREATE TABLE IF NOT EXISTS rewiews (photo_rewiew blob)')
    def user_exists(self, user_id):
        with self.conn:
            result = self.cur.execute('SELECT * FROM all_users WHERE cid=?', (user_id,)).fetchmany(1)
            return bool(len(result))

    def user_blocked(self, user_id):
        with self.conn:
            result = self.cur.execute('SELECT * FROM blocked_users WHERE cid=?', (user_id,)).fetchmany(1)
            return bool(len(result))
    def query(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        self.conn.commit()

    def fetchone(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchall()

    def __del__(self):
        self.conn.close()


'''

products: idx text, title text, body text, photo blob, price int, tag text

orders: cid int, usr_name text, usr_address text, products text

cart: cid int, idx text, quantity int ==> product_idx

categories: idx text, title text

wallet: cid int, balance real

questions: cid int, question text

'''
