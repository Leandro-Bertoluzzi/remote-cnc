import mocks.grbl as grbl_mocks
import pytest
from core.utilities.grbl.constants import GrblActiveState
from core.utilities.grbl.grblStatus import GrblStatus


class TestGrblStatus:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.grbl_status = GrblStatus()

    def test_getters(self):
        # Set test values for controller's parameters
        self.grbl_status._state["status"] = grbl_mocks.grbl_status
        self.grbl_status._state["parserstate"] = grbl_mocks.grbl_parserstate

        # Call methods under test
        status = self.grbl_status.get_status_report()
        machine_position = self.grbl_status.get_position("mpos")
        work_position = self.grbl_status.get_position("wpos")
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
        "active_state",
        [
            GrblActiveState.IDLE.value,
            GrblActiveState.RUN.value,
            GrblActiveState.HOLD.value,
            GrblActiveState.DOOR.value,
            GrblActiveState.HOME.value,
            GrblActiveState.SLEEP.value,
            GrblActiveState.ALARM.value,
            GrblActiveState.CHECK.value,
        ],
    )
    def test_status_checkers(self, active_state):
        # Set test value for controller's active state
        self.grbl_status._state["status"]["activeState"] = active_state

        # Call methods under test
        is_alarm = self.grbl_status.is_alarm()
        is_idle = self.grbl_status.is_idle()
        is_checkmode = self.grbl_status.is_checkmode()

        # Assertions
        assert is_alarm == (active_state == GrblActiveState.ALARM.value)
        assert is_idle == (active_state == GrblActiveState.IDLE.value)
        assert is_checkmode == (active_state == GrblActiveState.CHECK.value)

    # ------------------------------------------------------------------ #
    # update_status: carry-forward & position derivation                 #
    # ------------------------------------------------------------------ #

    def test_update_status_carry_forward_wco(self):
        """WCO is only emitted periodically; the previous value must be carried forward."""
        # Establish a previous WCO.
        self.grbl_status.update_status(
            {"mpos": {"x": 0.0, "y": 0.0, "z": 0.0}, "wco": {"x": 1.0, "y": 2.0, "z": 3.0}}
        )

        # New report without WCO.
        self.grbl_status.update_status({"mpos": {"x": 5.0, "y": 5.0, "z": 5.0}})

        assert self.grbl_status._state["status"]["wco"] == {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_update_status_carry_forward_ov(self):
        """Override values are only in *override* reports; must be carried forward."""
        self.grbl_status.update_status(
            {"mpos": {"x": 0.0, "y": 0.0, "z": 0.0}, "ov": [110, 100, 100]}
        )

        # New report without 'ov'.
        self.grbl_status.update_status({"mpos": {"x": 1.0, "y": 0.0, "z": 0.0}})

        assert self.grbl_status._state["status"]["ov"] == [110, 100, 100]

    def test_update_status_carry_forward_accessory_state(self):
        """accessoryState must be carried forward when absent from the new report."""
        self.grbl_status.update_status(
            {"mpos": {"x": 0.0, "y": 0.0, "z": 0.0}, "accessoryState": "S"}
        )

        self.grbl_status.update_status({"mpos": {"x": 1.0, "y": 0.0, "z": 0.0}})

        assert self.grbl_status._state["status"]["accessoryState"] == "S"

    def test_update_status_derives_wpos_from_mpos(self):
        """When only mpos is present, wpos must be derived as mpos - wco."""
        wco = {"x": 1.0, "y": 2.0, "z": 3.0}
        mpos = {"x": 10.0, "y": 12.0, "z": 13.0}

        self.grbl_status.update_status({"mpos": mpos, "wco": wco})

        expected_wpos = {"x": 9.0, "y": 10.0, "z": 10.0}
        assert self.grbl_status._state["status"]["wpos"] == expected_wpos

    def test_update_status_derives_mpos_from_wpos(self):
        """When only wpos is present, mpos must be derived as wpos + wco."""
        wco = {"x": 1.0, "y": 2.0, "z": 3.0}
        # First call to establish WCO.
        self.grbl_status.update_status({"wpos": {"x": 0.0, "y": 0.0, "z": 0.0}, "wco": wco})

        # Second call: only wpos, WCO carried forward.
        wpos = {"x": 9.0, "y": 10.0, "z": 10.0}
        self.grbl_status.update_status({"wpos": wpos})

        expected_mpos = {"x": 10.0, "y": 12.0, "z": 13.0}
        assert self.grbl_status._state["status"]["mpos"] == expected_mpos

    def test_update_status_no_derivation_when_both_present(self):
        """When both mpos and wpos are supplied, neither is overwritten."""
        mpos = {"x": 5.0, "y": 5.0, "z": 5.0}
        wpos = {"x": 4.0, "y": 4.0, "z": 4.0}
        wco = {"x": 1.0, "y": 1.0, "z": 1.0}

        self.grbl_status.update_status({"mpos": mpos, "wpos": wpos, "wco": wco})

        # Both values must be exactly what was supplied — no derivation.
        assert self.grbl_status._state["status"]["mpos"] == mpos
        assert self.grbl_status._state["status"]["wpos"] == wpos
