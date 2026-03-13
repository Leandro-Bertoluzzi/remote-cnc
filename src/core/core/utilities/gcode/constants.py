# VALID COMMAND CODES

'''
List of Supported G-Codes in Grbl v1.1:
  - Non-Modal Commands: G4, G10L2, G10L20, G28, G30, G28.1, G30.1, G53, G92, G92.1
  - Motion Modes: G0, G1, G2, G3, G38.2, G38.3, G38.4, G38.5, G80
  - Feed Rate Modes: G93, G94
  - Unit Modes: G20, G21
  - Distance Modes: G90, G91
  - Arc IJK Distance Modes: G91.1
  - Plane Select Modes: G17, G18, G19
  - Tool Length Offset Modes: G43.1, G49
  - Cutter Compensation Modes: G40
  - Coordinate System Modes: G54, G55, G56, G57, G58, G59
  - Control Modes: G61
  - Program Flow: M0, M1, M2, M30*
  - Coolant Control: M7*, M8, M9
  - Spindle Control: M3, M4, M5
  - Valid Non-Command Words: F, I, J, K, L, N, P, R, S, T, X, Y, Z
  (*) Commands not enabled by default in config.h
'''

GCODE_VALID_GCODES = [
    'G0', 'G1', 'G2', 'G3', 'G38.2', 'G38.3', 'G38.4', 'G38.5', 'G80',    # Motion Modes
    'G4', 'G10', 'G28', 'G30', 'G28.1', 'G30.1', 'G53', 'G92', 'G92.1',   # Non-Modal Commands
    'G93', 'G94',                                                         # Feed Rate Modes
    'G20', 'G21',                                                         # Unit modes
    'G90', 'G91',                                                         # Distance modes
    'G91.1',                                                        # Arc IJK Distance Modes
    'G17', 'G18', 'G19',                                            # Plane Select Modes
    'G43.1', 'G49',                                                 # Tool Length Offset Modes
    'G40',                                                          # Cutter Compensation Modes
    'G54', 'G55', 'G56', 'G57', 'G58', 'G59',                       # Coordinate System Modes
    'G61',                                                          # Control Modes
    'G00', 'G01', 'G02', 'G03', 'G04',                              # Alternative syntax for codes
]

GCODE_VALID_MCODES = [
    'M0', 'M1', 'M2', 'M00', 'M01', 'M02', 'M30',  # Program Flow
    'M7', 'M8', 'M9', 'M07', 'M08', 'M09',         # Coolant Control
    'M3', 'M4', 'M5', 'M03', 'M04', 'M05',         # Spindle Control
]

GCODE_PROGRAM_END_CODES = ['M2', 'M02', 'M30']
