from mocks import grbl_mocks

task_metadata_in_progress = {
    'status': 'PROGRESS',
    'result': {
        'sent_lines': 15,
        'processed_lines': 10,
        'total_lines': 20,
        'status': grbl_mocks.grbl_status,
        'parserstate': grbl_mocks.grbl_parserstate
    }
}

task_metadata_failure = {
    'status': 'FAILURE',
    'result': 'Mocked error message'
}

task_metadata_success = {
    'status': 'SUCCESS',
    'result': {}
}
