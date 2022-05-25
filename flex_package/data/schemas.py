"""
The data schemas used in the model.
"""

import pandera as pa
from pandera.typing import Series


class OutSchema(pa.SchemaModel):
    """
    Output format of main data preparation set.
    """

    date: Series[pa.DateTime]
    year: Series[int] = pa.Field(ge=0)
    weekday: Series[str] = pa.Field(isin=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
