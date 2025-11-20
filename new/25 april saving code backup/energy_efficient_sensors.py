def select_optimal_sensors(task_requirements, context):
    # Example logic based on task requirements
    if task_requirements['data_type'] == 'visual' and context['time_of_day'] == 'night':
        return {'sensor_type': 'Infrared', 'config': 'low_power'}
    else:
        return {'sensor_type': 'Camera', 'config': 'high_resolution'}
