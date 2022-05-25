"""
Example: Testing the data preparation functions.
"""

import pandas as pd

from flex_package.data.prepare_data import set_datetime_columns


data = pd.DataFrame(data={
    'date': ['2021-12-01', '2021-12-02', '2021-12-03']
})


def test_set_datetime_columns():
    """Example: Test function `test_set_datetime_columns()`. Test whether all datetime columns are set.
    """

    df = set_datetime_columns(data)
    columns = ['date', 'year', 'weekday']
    assert all(column in df.columns for column in columns)
