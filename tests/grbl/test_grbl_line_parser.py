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
                '[G38.2 G54 G17 G21 G91 G94 M0 M5 M9 T0 F20. S0.]',
                (
                    'GrblMsgParserState',
                    {
                        'modal': {
                            'motion': 'G38.2',
                            'wcs': 'G54',
                            'plane': 'G17',
                            'units': 'G21',
                            'distance': 'G91',
                            'feedrate': 'G94',
                            'program': 'M0',
                            'spindle': 'M5',
                            'coolant': 'M9'
                        },
                        'tool': '0',
                        'feedrate': '20.',
                        'spindle': '0.',
                        'raw': '[G38.2 G54 G17 G21 G91 G94 M0 M5 M9 T0 F20. S0.]'
                    }
                )
            ),
            (
                '[GC:G38.2 G54 G17 G21 G91 G94 M0 M5 M9 T0 F20. S0.]',
                (
                    'GrblMsgParserState',
                    {
                        'modal': {
                            'motion': 'G38.2',
                            'wcs': 'G54',
                            'plane': 'G17',
                            'units': 'G21',
                            'distance': 'G91',
                            'feedrate': 'G94',
                            'program': 'M0',
                            'spindle': 'M5',
                            'coolant': 'M9'
                        },
                        'tool': '0',
                        'feedrate': '20.',
                        'spindle': '0.',
                        'raw': '[GC:G38.2 G54 G17 G21 G91 G94 M0 M5 M9 T0 F20. S0.]'
                    }
                )
            ),
            (
                '[GC:G38.2 G54 G17 G21 G91 G94 M0 M5 M7 M8 T0 F20. S0.]',
                (
                    'GrblMsgParserState',
                    {
                        'modal': {
                            'motion': 'G38.2',
                            'wcs': 'G54',
                            'plane': 'G17',
                            'units': 'G21',
                            'distance': 'G91',
                            'feedrate': 'G94',
                            'program': 'M0',
                            'spindle': 'M5',
                            'coolant': ['M7', 'M8']
                        },
                        'tool': '0',
                        'feedrate': '20.',
                        'spindle': '0.',
                        'raw': '[GC:G38.2 G54 G17 G21 G91 G94 M0 M5 M7 M8 T0 F20. S0.]'
                    }
                )
            ),
            (
                '<Idle|MPos:3.000,2.000,0.000|F:0>',
                (
                    'GrblMsgStatus',
                    {
                        'activeState': 'Idle',
                        'mpos': {'x': 3.0, 'y': 2.0, 'z': 0.0},
                        'feedrate': 0.0,
                        'raw': '<Idle|MPos:3.000,2.000,0.000|F:0>'
                    }
                )
            ),
            (
                '<Hold:0|MPos:5.000,2.000,0.000|FS:0,0>',
                (
                    'GrblMsgStatus',
                    {
                        'activeState': 'Hold',
                        'subState': 0,
                        'mpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
                        'feedrate': 0.0,
                        'spindle': 0,
                        'raw': '<Hold:0|MPos:5.000,2.000,0.000|FS:0,0>'
                    }
                )
            ),
            (
                '<Idle|MPos:5.000,2.000,0.000|FS:0,0|Ov:100,100,100>',
                (
                    'GrblMsgStatus',
                    {
                        'activeState': 'Idle',
                        'mpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
                        'feedrate': 0.0,
                        'spindle': 0,
                        'ov': [100, 100, 100],
                        'raw': '<Idle|MPos:5.000,2.000,0.000|FS:0,0|Ov:100,100,100>'
                    }
                )
            ),
            (
                '<Idle|MPos:5.000,2.000,0.000|FS:0.0,0|WCO:0.000,0.000,0.000>',
                (
                    'GrblMsgStatus',
                    {
                        'activeState': 'Idle',
                        'mpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
                        'feedrate': 0.0,
                        'spindle': 0,
                        'wco': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                        'raw': '<Idle|MPos:5.000,2.000,0.000|FS:0.0,0|WCO:0.000,0.000,0.000>'
                    }
                )
            ),
            (
                '<Run|MPos:23.036,1.620,0.000|FS:500,0>',
                (
                    'GrblMsgStatus',
                    {
                        'activeState': 'Run',
                        'mpos': {'x': 23.036, 'y': 1.620, 'z': 0.0},
                        'feedrate': 500.0,
                        'spindle': 0,
                        'raw': '<Run|MPos:23.036,1.620,0.000|FS:500,0>'
                    }
                )
            ),
            (
                '<Hold:0|MPos:5.000,2.000,0.000|WPos:5.000,2.000,0.000|FS:0.0,0|WCO:0.000,0.000,0.000|Pn:XYZPDHRS|Bf:15,128|Ln:90|Ov:100,100,100|A:SFM>',
                (
                    'GrblMsgStatus',
                    {
                        'activeState': 'Hold',
                        'subState': 0,
                        'mpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
                        'wpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
                        'feedrate': 0.0,
                        'spindle': 0,
                        'wco': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                        'pinstate': 'XYZPDHRS',
                        'buffer': {'planner': 15, 'rx': 128},
                        'line': 90,
                        'ov': [100, 100, 100],
                        'accessoryState': 'SFM',
                        'raw': '<Hold:0|MPos:5.000,2.000,0.000|WPos:5.000,2.000,0.000|FS:0.0,0|WCO:0.000,0.000,0.000|Pn:XYZPDHRS|Bf:15,128|Ln:90|Ov:100,100,100|A:SFM>'
                    }
                )
            ),
            (
                'invalid',
                (None, {'raw': 'invalid'})
            )
        ]
    )
def test_grbl_parser(message, expected):
    assert GrblLineParser.parse(message) == expected
