session_states = {}

def get_state(session_id: str) -> dict:
    return session_states.get(session_id, {})

def update_state(session_id: str, data: dict) -> None:
    session_states[session_id] = {**get_state(session_id), **data}

def clear_state(session_id: str) -> None:
    if session_id in session_states:
        del session_states[session_id]

# client type changing for mvp
user_client_types = {}


def set_user_client_type(user_id: str, client_type: str) -> None:
    user_client_types[user_id] = client_type


def get_user_client_type(user_id: str, default: str = "restaurant") -> str:
    return user_client_types.get(user_id, default)