from grbl.constants import GrblActiveState
from grbl.grblStatus import GrblStatus
import mocks.grbl_mocks as grbl_mocks
import pytest


class TestGrblStatus:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.grbl_status = GrblStatus()

    def test_getters(self):
        # Set test values for controller's parameters
        self.grbl_status._state['status'] = grbl_mocks.grbl_status
        self.grbl_status._state['parserstate'] = grbl_mocks.grbl_parserstate

        # Call methods under test
        status = self.grbl_status.get_status_report()
        machine_position = self.grbl_status.get_mpos()
        work_position = self.grbl_status.get_wpos()
        parser_state = self.grbl_status.get_parser_state()
        modal_group = self.grbl_status.get_modal()
        tool = self.grbl_status.get_tool()
        feedrate = self.grbl_status.get_feedrate()
        spindle = self.grbl_status.get_spindle()

        # Assertions
        assert status == grbl_mocks.grbl_status
        assert machine_position == grbl_mocks.grbl_machine_position
        assert work_position == grbl_mocks.grbl_work_position
        assert parser_state == grbl_mocks.grbl_parserstate
        assert modal_group == grbl_mocks.grbl_modal
        assert tool == grbl_mocks.grbl_tool_index
        assert feedrate == grbl_mocks.grbl_feedrate
        assert spindle == grbl_mocks.grbl_spindle

    @pytest.mark.parametrize(
        'active_state',
        [
            GrblActiveState.IDLE.value,
            GrblActiveState.RUN.value,
            GrblActiveState.HOLD.value,
            GrblActiveState.DOOR.value,
            GrblActiveState.HOME.value,
            GrblActiveState.SLEEP.value,
            GrblActiveState.ALARM.value,
            GrblActiveState.CHECK.value
        ]
    )
    def test_status_checkers(self, active_state):
        # Set test value for controller's active state
        self.grbl_status._state['status']['activeState'] = active_state

        # Call methods under test
        is_alarm = self.grbl_status.is_alarm()
        is_idle = self.grbl_status.is_idle()
        is_checkmode = self.grbl_status.is_checkmode()

        # Assertions
        assert is_alarm == (active_state == GrblActiveState.ALARM.value)
        assert is_idle == (active_state == GrblActiveState.IDLE.value)
        assert is_checkmode == (active_state == GrblActiveState.CHECK.value)
