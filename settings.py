from communicator import Arduino, Bridge

PLOTS = 4
LIMITS = {'counter': (0, 10000), 
          'thrust_force_0': (-500, 500), 
          'thrust_force_1': (-500, 500), 
          'thrust_force_2': (-500, 500),
          'thrust_force_3': (-500, 500), 
          'lift_force_0': (-1500, 1500), 
          'lift_force_1': (-1500, 1500), 
          'lift_force_2': (-1500, 1500),
          'lift_force_3': (-1500, 1500), 
          'yaw': (-90, 90),
          'pitch': (-10, 15),
          'roll': (-5, 5), 
          'fcnt': (0, 64), 
          'timer': (0, 10), 
          'voltage': (0, 14), 
          'current': (0, 10), 
          'rpm': (0, 5000)}
COMS = [{'name': 'thrust_bridge', 'type': Bridge, 'series_prefix': 'thrust'},
        {'name': 'arduino', 'type': Arduino, 'series_prefix': ''},
        {'name': 'lift_bridge', 'type': Bridge, 'series_prefix':'lift'} 
        ]
SAMPLE_RATE = 50 #hz
DRAW_RATE = 10 #hz
