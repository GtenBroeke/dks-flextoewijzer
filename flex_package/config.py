# ----------------------------------------------------------------------------------------------------------------------
# RUN SETTINGS
# ----------------------------------------------------------------------------------------------------------------------
# Boolean indicating whether the prepared data should be updated (True) or retrieved from the storage (False)
BOOL_UPDATE_DATA = False

# Boolean indicating whether the data should be written to the storage (True) or not (False)
BOOL_WRITE_TO_STORAGE = False

# Log level. Typical values are ERROR, WARNING, INFO, DEBUG
LOG_LEVEL = 'DEBUG'

# Select all the packages for which you want to report the logs in a list, for example ['package'] or
# ['package1', 'package2']. Alternatively you can set LOGGERS = ['ALL'], which will report logging of all packages.
LOGGERS = ['flex_package']

# ----------------------------------------------------------------------------------------------------------------------
# FILE PATHS
# ----------------------------------------------------------------------------------------------------------------------
PATH_STORAGE = 's3://postnl-datalake-dks/scds/dks-flextoewijzer'

# Input files
PATH_INPUT = f'{PATH_STORAGE}/input'
PATH_ADDRESSES = f'{PATH_INPUT}/adressen_lijst.csv'
PATH_DEPARTURE_TIMES = f'{PATH_INPUT}/final_departure_times.csv'
PATH_DEPOT_DATA = f'{PATH_INPUT}/PostNL_depots.xlsx'
PATH_AFVOER = f'{PATH_INPUT}/31_01_2022/afvoerbehoefte_voorspeller_scenario_20220131_scans.csv'
PATH_SCANS = f'{PATH_INPUT}/31_01_2022/afvoerbehoefte_voorspeller_scenario_20220131_scans.csv'
PATH_TRANSPORT = f'{PATH_INPUT}/31_01_2022/VAR-20210131.csv'
PATH_REGISTRATIE = f'{PATH_INPUT}/31_01_2022/31-01-2022 Registratie_mod.xlsx'

# Interim files
PATH_INTERIM = f'{PATH_STORAGE}/interim'
PATH_AFVOER_BASELINE = f'{PATH_INTERIM}/afvoer_baseline.xlsx'
PATH_TRANSPORT_CLEANED = f'{PATH_INTERIM}/VAR.csv'

# Output files
PATH_OUTPUT = f'{PATH_STORAGE}/output'
PATH_AFVOER_ORDERS = f'{PATH_OUTPUT}/afvoer_orders.xlsx'

# Monitoring files
PATH_MONITORING = f'{PATH_STORAGE}/monitoring'
PATH_MONITORING_DATA = f'{PATH_OUTPUT}/my_monitoring_data.csv'

# ----------------------------------------------------------------------------------------------------------------------
# MODEL PARAMETERS
# ----------------------------------------------------------------------------------------------------------------------
import datetime
rc_threshold = 48
rc_threshold_future = 48
truck_capacity = 48
w1 = 1
process_day = datetime.date(2022, 1, 31)

start_time = datetime.datetime(year=2022, month=1, day=31, hour=8)
end_time = datetime.datetime(year=2022, month=2, day=1, hour=7)
current_time = datetime.datetime(year=2022, month=2, day=1, hour=2)