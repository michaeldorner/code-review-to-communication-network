import bz2

import pandas as pd
from numpy import ndarray
import orjson


def create_communication_channels(human_activities, t_1, t_2, code_review_col='pr_id', participant_col='user_id'):

    first = human_activities.sort_values('timestamp').groupby(code_review_col).timestamp.first()
    last = human_activities.sort_values('timestamp').groupby(code_review_col).timestamp.last()

    left_is_complete = (first >= t_1) & (first < t_2)
    right_is_complete = (last >= t_1) & (last < t_2)

    bounded = (left_is_complete & right_is_complete).rename('bounded')
    left_bounded = (left_is_complete & ~right_is_complete).rename('left-bounded')
    right_bounded = (~left_is_complete & right_is_complete).rename('right-bounded')
    unbounded = (~left_is_complete & ~right_is_complete).rename('unbounded')

    boolean_bound = pd.concat([left_bounded, right_bounded, bounded, unbounded], axis=1)
    bounds = boolean_bound.dot(boolean_bound.columns).rename('bound')

    sampled_activities = human_activities[(human_activities.timestamp >= t_1) & (human_activities.timestamp < t_2)]
    start = sampled_activities.groupby(code_review_col).timestamp.min().rename('start')
    end = sampled_activities.groupby(code_review_col).timestamp.max().rename('end')
    participants = sampled_activities.groupby(code_review_col)[participant_col].unique().rename('participants')

    communication_channels = pd.concat([start, end, participants], axis=1).join(bounds)
    communication_channels.info()

    return communication_channels


def store_communication_channels(communication_channels, file_path):
    def default(obj):
        match obj:
            case pd.Timestamp():
                return obj.to_pydatetime()
            case ndarray():
                return obj.tolist()
            case _:
                raise TypeError
    byte_data = bz2.compress(orjson.dumps(communication_channels.to_dict(orient='index'), default=default, option=orjson.OPT_SORT_KEYS | orjson.OPT_SERIALIZE_NUMPY))
    with open(file_path, 'wb') as file_handle:
        file_handle.write(byte_data)
