from communicator import Arduino, Bridge

PLOTS = 4
LIMITS = {'counter': (0, 1000), 
          'yaxis': (0, 1023), 
          'thrust_force_0': (-200, 1000), 
          'thrust_force_1': (-200, 1000), 
          'thrust_force_2': (-200, 1000),
          'thrust_force_3': (-200, 1000), 
          'lift_force_0': (-200, 500), 
          'lift_force_1': (-200, 500), 
          'lift_force_2': (-200, 500),
          'lift_force_3': (-200, 500), 
          'yaw': (-90, 90),
          'pitch': (-90, 90),
          'roll': (-90, 90), 
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
