import flex_package.models.modelfunctions.flexvoorspeller_functions as mf
import flex_package.config as config
import pandas as pd
import logging
import flex_package.visualization.visualize as vis

logger = logging.getLogger(__name__)


def main():
    logger.info('Order generation - started')

    # Read data from prediction from day before
    xls = pd.ExcelFile(config.PATH_AFVOER_BASELINE)

    # Read transport data
    inter_transports = mf.read_cleaned_VAR_data(config.PATH_TRANSPORT_CLEANED)

    afvoer_dict = dict()  # Dictionary will contain predicted afvoer and predictions of RC on floor for each depot
    for name in xls.sheet_names[2:]:     # Loop over all combinations of depot and destination
        origin = name.split(sep='-')[0]
        destination = name.split(sep='-')[1]
        logger.info(origin, destination)

        # Obtain dfs containing predicted number of RC afvoer from depot and planned inter transports
        afvoer = xls.parse(sheet_name=name)
        df_inter = mf.generate_inter_df(origin, destination, inter_transports)

        # Get current number of RC on the floor for the destination of interest
        rc_floor = mf.get_floor_stock(origin, destination, config.current_time, afvoer)
        # Update the predictions for the afvoer by incorporating the latest version of planned inter transports
        afvoer = mf.update_inter_transports(afvoer, df_inter, config.current_time, config.truck_capacity)
        # Update the predictions for the afvoer by incorporating the current number of RC on the depot floor
        afvoer = mf.update_afvoer(afvoer, config.current_time, rc_floor)
        # Create flex orders, and add these to the afvoer predictions
        afvoer, afvoer_orders = mf.add_flex_orders(afvoer, config.current_time, origin, destination)

        # Save the predictions in a dictionary
        afvoer_dict[name] = afvoer
    logger.info('Order generation - computations done')

    # Below we save a dataframe with information for all generated flex orders and with the predicted afvoer for each
    # depot and each destination
    df_orders = pd.DataFrame(columns=['Time', 'Origin', 'Destination', 'Size'])
    for order in afvoer_orders:
        row = pd.DataFrame([[order.Time, order.Origin, order.Destination, order.Size]], columns=df_orders.columns)
        df_orders = pd.concat([df_orders, row])
    output_path = config.PATH_AFVOER_ORDERS
    with pd.ExcelWriter(output_path) as writer:
        df_orders.to_excel(writer, sheet_name='afvoerorders')
        for key in afvoer_dict.keys():
            afvoer_dict[key].to_excel(writer, sheet_name=key, index=False)
    logger.info('Order generation - results saved')


if __name__ == '__main__':
    main()

