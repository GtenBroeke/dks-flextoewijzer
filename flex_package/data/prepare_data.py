"""
Module to prepare data set A, which is retrieved from source B.
"""

import logging
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame
import datetime

from flex_package.data.schemas import OutSchema
from flex_package import config

logger = logging.getLogger(__name__)


@pa.check_types
def get_transport_data(update_data: bool = True, write_data: bool = True) -> pd.DataFrame:
    """Retrieve prepared data.

    Args:
        update_data: Boolean indicating whether the data should be updated (True) or retrieved from storage (False).
        write_data: Boolean indicating whether the data should be written to S3 (True) or not (False).

    Returns:
        Prepared data set.
    """

    if update_data:
        logger.debug('Import raw data')
        data = pd.read_csv(config.PATH_TRANSPORT, sep=';', encoding="utf-8", decimal=',')

        logger.debug('Convert data columns')
        data = set_datetime_column(data)
        data = select_inter(data)
        data = filter_by_time(data)
        data = rename_locations(data)
        data = filter_by_status(data)
        data = select_columns(data)
        data['RC groot equivalent gepland'] = pd.to_numeric(data['RC groot equivalent gepland'])
        if write_data:
            logger.debug('Write data to S3')
            data.to_csv(config.PATH_TRANSPORT_CLEANED, index=False)
    else:
        logger.debug('Retrieve prepared data')
        data = pd.read_csv(config.PATH_INTERIM_DATA)

    return data


def get_transport_data_SIM(update_data: bool = True, write_data: bool = True) -> pd.DataFrame:
    """Retrieve prepared data.

    Args:
        update_data: Boolean indicating whether the data should be updated (True) or retrieved from storage (False).
        write_data: Boolean indicating whether the data should be written to S3 (True) or not (False).

    Returns:
        Prepared data set.
    """

    if update_data:
        logger.debug('Import raw data')
        data = pd.read_excel(config.PATH_TRANSPORT_SIM)

        logger.debug('Convert data columns')
        data = set_datetime_column_SIM(data)
        data = filter_by_time(data)
        data = add_destination(data)
        data = select_inter_SIM(data)
        depot_data = pd.read_excel(config.PATH_DEPOT_DATA, sheet_name='DepotData')

        data = convert_locations(data, depot_data)
        data = select_columns(data)
        data['RC groot equivalent gepland'] = pd.to_numeric(data['RC groot equivalent gepland'])
        if write_data:
            logger.debug('Write data to S3')
            data.to_csv(config.PATH_TRANSPORT_SIM_CLEANED, index=False)
    else:
        logger.debug('Retrieve prepared data')
        data = pd.read_csv(config.PATH_INTERIM_DATA)

    return data


def set_datetime_column(data: pd.DataFrame) -> pd.DataFrame:
    """Add datetime columns.

    Args:
        data: Data set to be converted.

    Returns:
        Input data set with datetime columns.
    """

    data['loading_time'] = data['Startdatum laden'] + ' ' + data['Starttijd laden']
    data['loading_time'] = data['loading_time'].apply(lambda x: datetime.datetime.strptime(x, '%d-%m-%Y %H:%M'))

    return data


def add_destination(data: pd.DataFrame) -> pd.DataFrame:
    """Add datetime columns.

    Args:
        data: Data set to be converted.

    Returns:
        Input data set with datetime columns.
    """

    data['destination'] = None
    data.sort_values(by=['Ritid', 'Stoplabel'], inplace=True)
    data.reset_index(inplace=True, drop=True)
    for ind, row in data.iterrows():
        if ind < len(data) - 1:
            if row['Ritid'] == data.loc[ind + 1, 'Ritid']:
                data.loc[ind, 'destination'] = data.loc[ind + 1, 'Locatienaam']
    data.dropna(axis=0, how='any', inplace=True)
    return data


def set_datetime_column_SIM(data: pd.DataFrame) -> pd.DataFrame:
    """Add datetime columns.

    Args:
        data: Data set to be converted.

    Returns:
        Input data set with datetime columns.
    """

    data['loading_time'] = data['geplandeeindtijd']
    #data['loading_time'] = data['loading_time'].apply(lambda x: datetime.datetime.strptime(x, '%d-%m-%Y %H:%M'))

    return data


def select_inter_SIM(data: pd.DataFrame) -> pd.DataFrame:
    data = data[data['ordersoort'] == 'INTER']
    #data.drop_duplicates(subset="Dagorder nummer", keep='first', inplace=True)
    return data


def select_inter(data: pd.DataFrame) -> pd.DataFrame:
    data = data[data['Operator service'].isin([70, 82])]
    data.drop_duplicates(subset="Dagorder nummer", keep='first', inplace=True)
    return data


def filter_by_time(data: pd.DataFrame) -> pd.DataFrame:
    data = data[data['loading_time'] > config.start_time]
    data = data[data['loading_time'] < config.end_time]

    return data


def rename_locations(data: pd.DataFrame) -> pd.DataFrame:
    data['Afk laadlocatie'] = data['Laadlocatie korte naam'].str.split('-').str[0]
    data['Afk loslocatie'] = data['Loslocatie korte naam'].str.split('-').str[0]
    data.loc[data['Loslocatie korte naam'] == 'EX-WW-KG', 'Afk loslocatie'] = 'XWW'
    data.loc[data['Laadlocatie korte naam'] == 'EX-WW-KG', 'Afk laadlocatie'] = 'XWW'
    data.loc[data['Loslocatie korte naam'] == 'ASD-CD', 'Afk loslocatie'] = 'XASD'
    data.loc[data['Laadlocatie korte naam'] == 'ASD-CD', 'Afk laadlocatie'] = 'XASD'
    data.loc[data['Loslocatie naam'] == 'Crossdock Tiel', 'Afk loslocatie'] = 'TL'
    data.loc[data['Laadlocatie naam'] == 'Crossdock Tiel', 'Afk laadlocatie'] = 'TL'

    return data


def convert_locations(data: pd.DataFrame, depot_data: pd.DataFrame) -> pd.DataFrame:
    data['Locatienaam'] = data['Locatienaam'].apply(lambda x: x.upper())
    data['destination'] = data['destination'].apply(lambda x: x.upper())
    data.replace(to_replace='CROSSDOCK AMSTERDAM', value='XASD', inplace=True)
    data.replace(to_replace='CROSSDOCK WAALWIJK', value='XWW', inplace=True)
    data.replace(to_replace=list(depot_data['SIM_NAME']), value=list(depot_data['Afk']), inplace=True)
    data['Afk laadlocatie'] = data['Locatienaam'].str.split('-').str[0]
    data['Afk laadlocatie'] = data['Afk laadlocatie'].replace(to_replace='TL', value='TIEL')
    data['Afk loslocatie'] = data['destination'].str.split('-').str[0]
    data['Afk loslocatie'] = data['Afk loslocatie'].replace(to_replace='TL', value='TIEL')
    return data


def filter_by_status(data: pd.DataFrame) -> pd.DataFrame:
    data = data[data['Status'] != 'Cancelled']
    data = data[data['Status'] != 'Cancelled_automatic']

    return data


def select_columns(data: pd.DataFrame) -> pd.DataFrame:
    selected_columns = ['Dagorder nummer', 'AAR nummer', 'Operator service', 'Status', 'RC groot equivalent gepland',
                        'RC groot equivalent geladen', 'loading_time', 'Afk laadlocatie', 'Afk loslocatie']
    data = data[selected_columns]

    return data


def select_columns(data: pd.DataFrame) -> pd.DataFrame:
    selected_columns = ['loading_time', 'Afk laadlocatie', 'Afk loslocatie']
    data = data[selected_columns]
    data['RC groot equivalent gepland'] = 48

    return data


if __name__ == '__main__':
    df = get_transport_data()
    df_sim = get_transport_data_SIM()
