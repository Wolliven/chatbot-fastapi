session_states = {}

def get_state(session_id: str) -> dict:
    return session_states.get(session_id, {})

def update_state(session_id: str, data: dict) -> None:
    session_states[session_id] = {**get_state(session_id), **data}

def clear_state(session_id: str) -> None:
    if session_id in session_states:
        del session_states[session_id]