celery_pong = [{
    'celery@node1': {'ok': 'pong'}
}]

celery_worker_pong = {
    'celery@node1': {'ok': 'pong'}
}

celery_worker_stats = {
    'celery@node1': {
        'total': {},
        'pid': 9156,
        'clock': '68',
        'uptime': 120,
        'pool': {
            'implementation': 'celery.concurrency.solo:TaskPool',
            'max-concurrency': 1,
            'processes': [9156],
            'max-tasks-per-child': None,
            'put-guarded-by-semaphore': True,
            'timeouts': []
        }, 'broker': {
            'hostname': 'localhost',
            'userid': None,
            'virtual_host': '0',
            'port': 6379,
            'insist': False,
            'ssl': False,
            'transport': 'redis',
            'connect_timeout': 4,
            'transport_options': {},
            'login_method': None,
            'uri_prefix': None,
            'heartbeat': 0,
            'failover_strategy': 'round-robin',
            'alternates': []
        }, 'prefetch_count': 32, 'rusage': 'N/A'
    }
}

celery_worker_registered_tasks = {
    'celery@node1': ['worker.tasks.executeTask']
}

celery_worker_active_tasks = {
    'celery@node1': ['worker.tasks.executeTask']
}

celery_worker_active_tasks_empty = {
    'celery@node1': []
}
