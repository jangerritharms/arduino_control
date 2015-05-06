from communicator import Arduino, Bridge

PLOTS = 4
LIMITS = {'counter': (0, 1000), 
          'yaxis': (0, 1023), 
          'thrust_force_0': (-0.1, 0.1), 
          'thrust_force_1': (-0.1, 0.1), 
          'thrust_force_2': (-0.1, 0.1), 
          'thrust_force_3': (-0.1, 0.1)}
COMS = [# {'name': 'thrust_bridge', 'type': Bridge, 'series_prefix': 'thrust'},
        {'name': 'arduino', 'type': Arduino, 'series_prefix': ''},
        #{'name': 'lift_bridge', 'type': Bridge} 
        ]

