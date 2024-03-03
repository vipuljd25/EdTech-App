def chapter_query(student_id, **kwargs):
    query = [
        {
            '$match': {
                'is_deleted': False,
                'status': "PUBLISHED",
                # 'chapter_id': 383,
                # 'subject_id_id': 168,
                **kwargs
            },
        },
        {
            '$lookup': {
                'from': "Students_App_chapterparts",
                'localField': "chapter_id",
                'foreignField': "chapter_id_id",
                'as': "chapter_parts",
            },
        },
        {
            '$unwind': {
                'path': "$chapter_parts",
                'preserveNullAndEmptyArrays': True,
            },
        },
        {
            '$replaceRoot': {
                'newRoot': "$chapter_parts",
            },
        },
        {
            '$match': {
                'is_deleted': False,
            },
        },
        {
            '$lookup': {
                'from': "data_points_partsprogress",
                'localField': "part_id",
                'foreignField': "part_id",
                'as': "part_progress",
            },
        },
        {
            '$project': {
                  'chapter_id_id': 1,
                  'part_id': 1,
                  'part_progress': {
                    '$filter': {
                      'input': "$part_progress",
                      'as': "progress",
                      'cond': {
                        '$eq': ["$$progress.student_id", student_id],
                      },
                    },
                  },
                }
        },
        {
            '$unwind': {
                'path': "$part_progress",
                'preserveNullAndEmptyArrays': True,
            },
        },
        {
            '$set': {
                "part_progress.student_id": student_id,
                "part_progress.chapter_id": "$chapter_id_id",
                "part_progress.part_id": "$part_id",
                "part_progress.subject_id": "$subject_id_id",
            },
        },
        {
            '$replaceRoot': {
                'newRoot': "$part_progress",
            },
        },
        {
            '$project': {
                'chapter_id': 1,
                '_id': 0,
                'part_id': 1,
                'student_id': 1,
                'percentage': {
                    '$ifNull': ["$percentage", 0],
                },
                'points': {
                    '$ifNull': ["$points", 0],
                },
                'time': {
                    '$ifNull': ["$time", 0],
                },
            },
        },
        {
            '$group': {
                '_id': "$chapter_id",
                'Percentage': {
                    '$avg': "$percentage",
                },
                'Points': {
                    '$sum': "$points",
                },
                'Minute': {
                    '$sum': "$time",
                },
            },
        },
    ]
    return query


def reels_query_total(student_id, **kwargs):
    query = [
        {
            '$match': {
                'student_id': student_id,
                **kwargs
            },
        },
        {
            '$group': {
                '_id': '$student_id',
                'QuestionsAttempt': {
                    '$sum': '$total_reels'
                },
                'correct': {
                    '$sum': '$correct'
                },
                'incorrect': {
                    '$sum': '$incorrect'
                },
                'time': {
                    '$sum': '$time'
                },
                'Points': {
                    '$sum': '$points'
                }
            }
        }

    ]
    return query


def reels_query_one(student_id, **kwargs):
    query = [
        {
            '$match': {
                'student_id': student_id,
                **kwargs
            },
        },
        {
            '$sort': {'created_at': -1}
        },
        {
            '$limit': 1
        },
        {
            "$project": {
                "QuestionsAttempt": "$total_reels",
                "Points": "$points"
            }
        }
    ]
    return query


def mcq_set_query(student_id, **kwargs):
    query = [
        {
            '$match': {
                'student_id': student_id,
                **kwargs  # subject_id, 'chapter_id'
            }
        },
        {
            '$count': 'Attempt'
        }
    ]
    return query


def lesson_component_query(student_id, **kwargs):
    query = [
        {
            '$match': {
                'student_id': student_id,
                'element_type': kwargs.get('element_type'),
                'created_at': {
                    '$gte': kwargs.get('start_date'),
                    '$lte': kwargs.get('end_date'),
                }
            }
        }, {
            '$group': {
                '_id': '$student_id',
                'Points': {
                    '$sum': '$points'
                },
                'Minute': {
                    '$sum': '$time'
                }
            }
        }
    ]
    return query


def earn_points_query(student_id, **kwargs):
    query = [
        {
            '$match': {
                'student_id': student_id,
                'created_at': {
                    '$gte': kwargs.get('start_date'),
                    '$lte': kwargs.get('end_date'),
                },
            }
        }, {
            '$group': {
                '_id': '$student_id',
                'Points': {
                    '$sum': '$points'
                }
            }
        }
    ]
    return query


def daily_open_query(student_id, **kwargs):
    query = [
        {
            '$match': {
                'point_activity': 'daily_open',
                'student_id': student_id,
                **kwargs
            }
        }, {
            '$group': {
                '_id': 'student_id',
                'day': {
                    '$sum': 1
                }
            }
        }
    ]
    return query


def highest_value_milestone_query(student_id, **kwargs):
    query = [
        {
            '$match': {
                'student_id': student_id
            }
        }, {
            '$lookup': {
                'from': 'data_points_milestones',
                'localField': 'milestone_id',
                'foreignField': '_id',
                'as': 'result'
            }
        }, {
            '$unwind': '$result'
        }, {
            '$match': {
                'result.milestone': kwargs.get('milestone_name')
            }
        }, {
            '$sort': {
                'result.value': -1
            }
        }, {
            '$limit': 1
        }, {
            '$project': {
                '_id': 0,
                'highestValueMilestone': {
                    '$ifNull': [
                        '$result.value', 0
                    ]
                }
            }
        }
    ]
    return query