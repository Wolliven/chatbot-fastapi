client_states = {}

def get_state(client):
    return client_states.get(client, {})

def update_state(client, data):
    client_states[client] = {**get_state(client), **data}

def clear_state(client):
    if client in client_states:
        del client_states[client]
