from utilities.grbl.grblUtils import build_jog_command, get_grbl_setting, is_setting_update_command, \
    JOG_DISTANCE_ABSOLUTE, JOG_DISTANCE_INCREMENTAL, JOG_UNIT_INCHES, JOG_UNIT_MILIMETERS
import pytest


@pytest.mark.parametrize(
        'parameters,expected',
        [
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 3.00,
                    'feedrate': 500.00,
                    'units': None,
                    'distance_mode': None,
                    'machine_coordinates': False
                },
                '$J=X1.0 Y2.0 Z3.0 F500.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 500.00,
                    'units': JOG_UNIT_INCHES,
                    'distance_mode': None,
                    'machine_coordinates': False
                },
                '$J=G20 X1.0 Y2.0 F500.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_MILIMETERS,
                    'distance_mode': None,
                    'machine_coordinates': False
                },
                '$J=G21 X1.0 Y2.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': None,
                    'distance_mode': JOG_DISTANCE_ABSOLUTE,
                    'machine_coordinates': False
                },
                '$J=G90 X1.0 Y2.0 Z0.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': None,
                    'distance_mode': JOG_DISTANCE_INCREMENTAL,
                    'machine_coordinates': False
                },
                '$J=G91 X1.0 Y2.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': None,
                    'distance_mode': None,
                    'machine_coordinates': True
                },
                '$J=G53 X1.0 Y2.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_INCHES,
                    'distance_mode': JOG_DISTANCE_ABSOLUTE,
                    'machine_coordinates': False
                },
                '$J=G90 G20 X1.0 Y2.0 Z0.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_MILIMETERS,
                    'distance_mode': JOG_DISTANCE_ABSOLUTE,
                    'machine_coordinates': False
                },
                '$J=G90 G21 X1.0 Y2.0 Z0.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_INCHES,
                    'distance_mode': JOG_DISTANCE_INCREMENTAL,
                    'machine_coordinates': False
                },
                '$J=G91 G20 X1.0 Y2.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_MILIMETERS,
                    'distance_mode': JOG_DISTANCE_INCREMENTAL,
                    'machine_coordinates': False
                },
                '$J=G91 G21 X1.0 Y2.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_INCHES,
                    'distance_mode': JOG_DISTANCE_ABSOLUTE,
                    'machine_coordinates': True
                },
                '$J=G53 G90 G20 X1.0 Y2.0 Z0.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_MILIMETERS,
                    'distance_mode': JOG_DISTANCE_ABSOLUTE,
                    'machine_coordinates': True
                },
                '$J=G53 G90 G21 X1.0 Y2.0 Z0.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_INCHES,
                    'distance_mode': JOG_DISTANCE_INCREMENTAL,
                    'machine_coordinates': True
                },
                '$J=G53 G91 G20 X1.0 Y2.0'
            ),
            (
                {
                    'x': 1.00,
                    'y': 2.00,
                    'z': 0.00,
                    'feedrate': 0.00,
                    'units': JOG_UNIT_MILIMETERS,
                    'distance_mode': JOG_DISTANCE_INCREMENTAL,
                    'machine_coordinates': True
                },
                '$J=G53 G91 G21 X1.0 Y2.0'
            ),
        ]
    )
def test_build_jog_command(parameters, expected):
    # Call the method under test
    response = build_jog_command(
        parameters['x'], parameters['y'], parameters['z'], parameters['feedrate'],
        units=parameters['units'],
        distance_mode=parameters['distance_mode'],
        machine_coordinates=parameters['machine_coordinates']
    )

    # Assertions
    assert response == expected


@pytest.mark.parametrize(
    'command,expected',
    [
        ('$23=5', True),
        ('$27=5.200', True),
        ('$27=', False),
        ('$text=5.200', False),
        ('$27=text', False),
        ('$$', False),
        ('invalid', False),
        ('$200=5', False),
    ]
)
def test_is_setting_update_command(command, expected):
    # Call the method under test
    response = is_setting_update_command(command)

    # Assertions
    assert response == expected


@pytest.mark.parametrize(
    'key,expected',
    [
        ('$0', {
            'setting': '$0',
            'message': 'Step pulse time',
            'units': 'microseconds',
            'description': 'Sets time length per step. Minimum 3usec.'
        }),
        ('$112', {
            'setting': '$112',
            'message': 'Z-axis maximum rate',
            'units': 'mm/min',
            'description': 'Z-axis maximum rate. Used as G0 rapid rate.'
        }),
        ('$200', None),
        ('invalid', None),
    ]
)
def test_get_grbl_setting(key, expected):
    # Call the method under test
    response = get_grbl_setting(key)

    # Assertions
    assert response == expected
