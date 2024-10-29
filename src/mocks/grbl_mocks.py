grbl_machine_position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
grbl_work_position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
grbl_wco = {'x': 0.0, 'y': 0.0, 'z': 0.0}

grbl_status = {
    'activeState': '',
    'mpos': grbl_machine_position,
    'wpos': grbl_work_position,
    'ov': [],
    'subState': None,
    'wco': grbl_wco,
    'pinstate': None,
    'buffer': None,
    'line': None,
    'accessoryState': None
}

grbl_modal = {
    'motion': 'G0',
    'wcs': 'G54',
    'plane': 'G17',
    'units': 'G21',
    'distance': 'G90',
    'feedrate': 'G94',
    'program': 'M0',
    'spindle': 'M5',
    'coolant': 'M9'
}

grbl_tool_index = 1
grbl_feedrate = 50.0
grbl_spindle = 250.0

grbl_parserstate = {
    'modal': grbl_modal,
    'tool': grbl_tool_index,
    'feedrate': grbl_feedrate,
    'spindle': grbl_spindle
}

grbl_init_message = 'Grbl 1.1h [\'$\' for help]'

grbl_settings = {
    '$0': {
        'value': '10',
        'message': 'Step pulse time',
        'units': 'microseconds',
        'description': 'Sets time length per step. Minimum 3usec.'
    },
    '$1': {
        'value': '25',
        'message': 'Step idle delay',
        'units': 'milliseconds',
        'description': 'Sets a short hold delay when stopping ...'
    }
}

grbl_parameters = {
    'G54': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G55': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G56': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G57': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G58': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G59': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G28': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G30': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'G92': {'x': 0.000, 'y': 0.000, 'z': 0.000},
    'TLO': 0.000,
    'PRB': {'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': True}
}

grbl_build_info = {
    'version': '1.1d',
    'comment': 'A comment',
    'optionCode': '',
    'blockBufferSize': 15,
    'rxBufferSize': 128
}
