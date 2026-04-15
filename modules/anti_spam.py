import time

user_history = {}

def is_spamming(user_id, content):
    now = time.time()
    if user_id not in user_history:
        user_history[user_id] = []
    
    # Keep only last 5 seconds of messages
    user_history[user_id] = [t for t in user_history[user_id] if now - t < 5]
    user_history[user_id].append(now)
    
    if len(user_history[user_id]) > 5:
        return True, "Too many messages (Fast)"
    
    return False, None
