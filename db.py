import redis

r_server = None

def open_db():
    global r_server
    if not r_server:
        r_server = redis.Redis("localhost")
        #if r_server.smembers('emails'): r_server.delete('emails')
    return r_server

def close_db():
    global r_server
    r_server.shutdown()