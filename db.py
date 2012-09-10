import redis

r_server = None

def test_redis_open():
    global r_server 
    return r_server.ping()

def open_db():
    global r_server
    if not r_server:
        r_server = redis.Redis("localhost")
        #if r_server.smembers('emails'): r_server.delete('emails')
    return r_server

def close_db():
    global r_server
    if r_server:
        r_server.shutdown()
    else:
        raise("No r_server db conn to close")