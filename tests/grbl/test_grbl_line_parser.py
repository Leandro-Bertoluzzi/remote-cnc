import pytest
from grbl.grblLineParser import GrblLineParser

@pytest.mark.parametrize(
        'message,expected',
        [
            (
                'ok',
                ('GrblResultOk', {'raw': 'ok'})
            ),
            (
                'error:17',
                ('GrblResultError', {'code': '17', 'message': 'Setting disabled', 'description': 'Laser mode requires PWM output.', 'raw': 'error:17'})
            ),
            (
                'ALARM:6',
                ('GrblMsgAlarm', {'code': '6', 'message': 'Homing fail', 'description': 'Homing fail. The active homing cycle was reset.', 'raw': 'ALARM:6'})
            ),
            (
                'Grbl 0.9j [\'$\' for help]',
                ('GrblMsgStartup', {'firmware': 'Grbl', 'version': '0.9j', 'message': " ['$' for help]", 'raw': "Grbl 0.9j ['$' for help]"})
            ),
            (
                'Grbl 1.1d [\'$\' for help]',
                ('GrblMsgStartup', {'firmware': 'Grbl', 'version': '1.1d', 'message': " ['$' for help]", 'raw': "Grbl 1.1d ['$' for help]"})
            ),
            (
                'Grbl 1.1',
                ('GrblMsgStartup', {'firmware': 'Grbl', 'version': '1.1', 'message': None, 'raw': "Grbl 1.1"})
            ),
            (
                'Grbl 1.1h: LongMill build [\'$\' for help]',
                ('GrblMsgStartup', {'firmware': 'Grbl', 'version': '1.1h', 'message': ": LongMill build [\'$\' for help]", 'raw': "Grbl 1.1h: LongMill build [\'$\' for help]"})
            ),
            (
                'Grbl 1.1h [\'$\' for help] LongMill build Feb 25, 2020',
                ('GrblMsgStartup', {'firmware': 'Grbl', 'version': '1.1h', 'message': " [\'$\' for help] LongMill build Feb 25, 2020", 'raw': "Grbl 1.1h [\'$\' for help] LongMill build Feb 25, 2020"})
            ),
            (
                'myCustomGrbl 2.0.0 [\'$\' for help]',
                ('GrblMsgStartup', {'firmware': 'myCustomGrbl', 'version': '2.0.0', 'message': " [\'$\' for help]", 'raw': "myCustomGrbl 2.0.0 [\'$\' for help]"})
            ),
            (
                '[HLP:$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x]',
                ('GrblMsgHelp', {'message': '$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x', 'raw': '[HLP:$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x]'})
            ),
            (
                '[MSG:Caution: Unlocked]',
                ('GrblMsgFeedback', {'message': 'Caution: Unlocked', 'raw': '[MSG:Caution: Unlocked]'})
            ),
            (
                '[echo:G1X0.540Y10.4F100]',
                ('GrblMsgEcho', {'message': 'G1X0.540Y10.4F100', 'raw': '[echo:G1X0.540Y10.4F100]'})
            ),
            (
                '[VER:1.1d.20161014:Some string]',
                ('GrblMsgVersion', {'version': '1.1d.20161014', 'comment': 'Some string', 'raw': '[VER:1.1d.20161014:Some string]'})
            ),
            (
                '[VER:1.1d.20161014:]',
                ('GrblMsgVersion', {'version': '1.1d.20161014', 'comment': '', 'raw': '[VER:1.1d.20161014:]'})
            ),
            (
                '[OPT:,15,128]',
                ('GrblMsgOptions', {'optionCode': '', 'blockBufferSize': '15', 'rxBufferSize': '128', 'raw': '[OPT:,15,128]'})
            ),
            (
                '[OPT:VL,15,128]',
                ('GrblMsgOptions', {'optionCode': 'VL', 'blockBufferSize': '15', 'rxBufferSize': '128', 'raw': '[OPT:VL,15,128]'})
            ),
            (
                '$N0=G54',
                ('GrblMsgUserDefinedStartup', {'name': '$N0', 'value': 'G54', 'raw': '$N0=G54'})
            ),
            (
                '$N0=G54 G00 G10',
                ('GrblMsgUserDefinedStartup', {'name': '$N0', 'value': 'G54 G00 G10', 'raw': '$N0=G54 G00 G10'})
            ),
            (
                '$10=100.200',
                ('GrblMsgSetting', {'name': '$10', 'value': '100.200', 'raw': '$10=100.200'})
            ),
            (
                '[G54:0.000,0.000,0.000]',
                ('GrblMsgParams', {'name': 'G54', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G54:0.000,0.000,0.000]'})
            ),
            (
                '[TLO:0.000]',
                ('GrblMsgParams', {'name': 'TLO', 'value': 0.000, 'raw': '[TLO:0.000]'})
            ),
            (
                '[PRB:0.000,0.000,0.000:0]',
                ('GrblMsgParams', {'name': 'PRB', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': False}, 'raw': '[PRB:0.000,0.000,0.000:0]'})
            ),
            (
                '[PRB:0.000,0.000,0.000:1]',
                ('GrblMsgParams', {'name': 'PRB', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': True}, 'raw': '[PRB:0.000,0.000,0.000:1]'})
            ),
            (
                'invalid',
                (None, {'raw': 'invalid'})
            )
        ]
    )
def test_grbl_parser(message, expected):
    assert GrblLineParser.parse(message) == expected
