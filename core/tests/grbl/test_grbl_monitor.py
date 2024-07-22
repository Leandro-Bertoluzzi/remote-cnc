from grbl.grblMonitor import GrblMonitor
from grbl.parsers.grblMsgTypes import GRBL_MSG_STATUS
import logging
from queue import Empty, Queue
import pytest


class TestGrblMonitor:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        self.grbl_logger = logging.getLogger('test_logger')

        # Mock logger methods
        mocker.patch.object(self.grbl_logger, 'addHandler')

        # Instantiate controller
        self.grbl_monitor = GrblMonitor(self.grbl_logger)

    @pytest.mark.parametrize('queue', [False, True])
    def test_debug(self, mocker, queue):
        # Mock methods
        mock_logger = mocker.patch.object(self.grbl_logger, 'debug')
        mock_queue = mocker.patch.object(self.grbl_monitor, 'queueLog')

        # Call method under test
        self.grbl_monitor.debug('Test message', queue)

        # Assertions
        assert mock_logger.call_count == 1
        assert mock_queue.call_count == (1 if queue else 0)

    @pytest.mark.parametrize('queue', [False, True])
    def test_info(self, mocker, queue):
        # Mock methods
        mock_logger = mocker.patch.object(self.grbl_logger, 'info')
        mock_queue = mocker.patch.object(self.grbl_monitor, 'queueLog')

        # Call method under test
        self.grbl_monitor.info('Test message', queue)

        # Assertions
        assert mock_logger.call_count == 1
        assert mock_queue.call_count == (1 if queue else 0)

    @pytest.mark.parametrize('queue', [False, True])
    def test_warning(self, mocker, queue):
        # Mock methods
        mock_logger = mocker.patch.object(self.grbl_logger, 'warning')
        mock_queue = mocker.patch.object(self.grbl_monitor, 'queueLog')

        # Call method under test
        self.grbl_monitor.warning('Test message', queue)

        # Assertions
        assert mock_logger.call_count == 1
        assert mock_queue.call_count == (1 if queue else 0)

    @pytest.mark.parametrize('queue', [False, True])
    def test_error(self, mocker, queue):
        # Mock methods
        mock_logger = mocker.patch.object(self.grbl_logger, 'error')
        mock_queue = mocker.patch.object(self.grbl_monitor, 'queueLog')

        # Call method under test
        self.grbl_monitor.error('Test message', queue)

        # Assertions
        assert mock_logger.call_count == 1
        assert mock_queue.call_count == (1 if queue else 0)

    @pytest.mark.parametrize('queue', [False, True])
    def test_critical(self, mocker, queue):
        # Mock methods
        mock_logger = mocker.patch.object(self.grbl_logger, 'critical')
        mock_queue = mocker.patch.object(self.grbl_monitor, 'queueLog')

        # Call method under test
        self.grbl_monitor.critical('Test message', exc_info=False, queue=queue)

        # Assertions
        assert mock_logger.call_count == 1
        assert mock_queue.call_count == (1 if queue else 0)

    @pytest.mark.parametrize('debug', [False, True])
    def test_sent(self, mocker, debug):
        # Mock methods
        mock_logger_debug = mocker.patch.object(self.grbl_logger, 'debug')
        mock_logger_info = mocker.patch.object(self.grbl_logger, 'info')
        mock_queue = mocker.patch.object(self.grbl_monitor, 'queueLog')

        # Call method under test
        self.grbl_monitor.sent('Test command', debug)

        # Assertions
        assert mock_logger_debug.call_count == (1 if debug else 0)
        assert mock_logger_info.call_count == (0 if debug else 1)
        assert mock_queue.call_count == (0 if debug else 1)

    @pytest.mark.parametrize('msgType', [GRBL_MSG_STATUS, 'AnotherType', None])
    def test_received(self, mocker, msgType):
        # Mock methods
        mock_logger_debug = mocker.patch.object(self.grbl_logger, 'debug')
        mock_logger_info = mocker.patch.object(self.grbl_logger, 'info')
        mock_queue = mocker.patch.object(self.grbl_monitor, 'queueLog')

        # Auxiliary variables
        debug = (msgType == GRBL_MSG_STATUS)

        # Call method under test
        self.grbl_monitor.received('Test message', msgType, {'key': 'value'})

        # Assertions
        assert mock_logger_debug.call_count == (2 if debug else 0)
        assert mock_logger_info.call_count == (0 if debug else 2)
        assert mock_queue.call_count == (0 if debug else 1)

    def test_queue_log(self, mocker):
        # Spy queue methods
        mock_queue = mocker.spy(Queue, 'put')

        # Call method under test
        self.grbl_monitor.queueLog('Testing...')

        # Assertions
        assert mock_queue.call_count == 1
        assert self.grbl_monitor.queue_log.get_nowait() == 'Testing...'

    @pytest.mark.parametrize(
            'amount,expected', [
                (0, False),
                (5, True)
            ])
    def test_queue_has_logs(self, mocker, amount, expected):
        # Mock queue methods
        mock_queue_size = mocker.patch.object(Queue, 'qsize', return_value=amount)

        # Call method under test
        response = self.grbl_monitor.hasLogs()

        # Assertions
        assert mock_queue_size.call_count == 1
        assert response == expected

    def test_get_queue_logs(self, mocker):
        # Mock queue contents
        self.grbl_monitor.queue_log.put('Log 1')
        self.grbl_monitor.queue_log.put('Log 2')
        self.grbl_monitor.queue_log.put('Log 3')

        # Spy queue methods
        mock_queue_get = mocker.spy(Queue, 'get_nowait')

        # Call method under test
        response = self.grbl_monitor.getLog()

        # Assertions
        assert mock_queue_get.call_count == 1
        assert response == 'Log 1'

    def test_get_queue_logs_empty(self, mocker):
        # Mock queue methods
        mock_queue_get = mocker.patch.object(
            Queue,
            'get_nowait',
            side_effect=Empty()
        )

        # Call method under test
        response = self.grbl_monitor.getLog()

        # Assertions
        assert mock_queue_get.call_count == 1
        assert response == ''
