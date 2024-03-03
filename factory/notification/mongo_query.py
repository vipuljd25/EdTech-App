
def device_token_from_studentchallengedata(**notification_data):
    query = [
        {
            '$match': {
                **notification_data
            }
        },
        {
            '$lookup': {
                'from': 'Students_App_devices',
                'localField': 'user_id',
                'foreignField': 'user_id',
                'as': 'result'
            }
        },
        {
            '$unwind': {
                'path': '$result',
                'preserveNullAndEmptyArrays': False
            }
        },
        {
            '$project': {
                '_id': 0,
                'result.token': 1
            }
        },
        {
            '$replaceRoot': {
                'newRoot': '$result'
            }
        }
    ]
    return query
