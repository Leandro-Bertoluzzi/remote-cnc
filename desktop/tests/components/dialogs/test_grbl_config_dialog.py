from components.dialogs.GrblConfigurationDialog import GrblConfigurationDialog
from PyQt5.QtWidgets import QDialogButtonBox, QTableWidget


class TestGrblConfigurationDialog:
    def test_grbl_configuration_dialog_init(self, qtbot, helpers):
        device_settings = {
            '$1': {
                'value': '1',
                'message': 'Step idle delay',
                'units': 'milliseconds',
                'description': 'Sets a short hold delay...'
            }
        }
        dialog = GrblConfigurationDialog(device_settings)
        qtbot.addWidget(dialog)

        # Assertions
        layout = dialog.layout()
        assert helpers.count_widgets(layout, QTableWidget) == 1
        assert helpers.count_widgets(layout, QDialogButtonBox) == 1
        assert dialog.settings.rowCount() == 1
        assert dialog.settings.columnCount() == 4
        assert dialog.settings.item(0, 0).text() == '1'
        assert dialog.settings.item(0, 1).text() == 'Step idle delay'
        assert dialog.settings.item(0, 2).text() == 'milliseconds'
        assert dialog.settings.item(0, 3).text() == 'Sets a short hold delay...'
        assert dialog.modifiedSettings == {}

    def test_grbl_configuration_dialog_update_table(self, qtbot):
        device_settings = {
            '$1': {
                'value': '1',
                'message': 'Step idle delay',
                'units': 'milliseconds',
                'description': 'Sets a short hold delay...'
            },
            '$2': {
                'value': '7',
                'message': 'Step pulse invert',
                'units': 'mask',
                'description': 'Inverts the step signal.'
            }
        }
        dialog = GrblConfigurationDialog(device_settings)
        qtbot.addWidget(dialog)

        # Interact with the widget
        dialog.settings.item(0, 0).setText('2')

        # Assertions
        assert dialog.modifiedSettings == {'$1': '2'}

    def test_grbl_configuration_dialog_get_modified_inputs(self, qtbot):
        device_settings = {
            '$1': {
                'value': '1',
                'message': 'Step idle delay',
                'units': 'milliseconds',
                'description': 'Sets a short hold delay...'
            },
            '$2': {
                'value': '7',
                'message': 'Step pulse invert',
                'units': 'mask',
                'description': 'Inverts the step signal.'
            }
        }
        dialog = GrblConfigurationDialog(device_settings)
        qtbot.addWidget(dialog)

        # Interact with the widget
        dialog.settings.item(0, 0).setText('2')
        response = dialog.getModifiedInputs()

        # Assertions
        assert dialog.modifiedSettings == {'$1': '2'}
        assert response == {'$1': '2'}
