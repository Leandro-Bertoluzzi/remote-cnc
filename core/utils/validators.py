valid_transitions = {
    'pending_approval': ['on_hold', 'cancelled'],
    'on_hold': ['in_progress', 'cancelled'],
    'in_progress': ['finished', 'failed'],
    'finished': [],
    'failed': ['pending_approval'],
    'cancelled': ['pending_approval']
}


def validate_transition(status: str, new_status: str):
    if new_status in valid_transitions[status]:
        return True
    else:
        return False
