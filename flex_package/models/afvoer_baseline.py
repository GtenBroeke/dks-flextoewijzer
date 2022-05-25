import pandas as pd
import flex_package.models.modelfunctions.flexvoorspeller_functions as mf
import flex_package.config as config
import logging

logger = logging.getLogger(__name__)


def main():
    logger.info('Baseline computation - started')
    # Read data from 'afvoerbehoeftevoorspeller'
    afvoer_behoefte = mf.read_afvoer_data(config.PATH_AFVOER)

    # Read VAR data for inter transport between the start and end time considered in the script
    path_VAR = config.PATH_TRANSPORT_CLEANED
    inter_transports = mf.read_cleaned_VAR_data(path_VAR)
    origin_list = afvoer_behoefte['origin'].unique()

    # Initialize DataFrame with the total deficit or surplus of transport for each depot-crossdock combination
    stock_dict = dict()    # Dictionary with the estimated number of RC present on the depot floor for all
                           # combinations of depot and destination

    # The loops below run over all combinations of depot and destination. For each combination, we get the expected
    # generated RC per 15 min. interval, and the planned inter transports. These are combined to estimate the number of
    # RC present on the floor for each depot and destination. This estimate is made per 15 minute interval.
    transport_deficiency = pd.DataFrame(0, index=origin_list, columns=afvoer_behoefte['crossdock'].unique())
    total_transport_diff = pd.DataFrame(0, index=origin_list, columns=afvoer_behoefte['crossdock'].unique())
    for Origin in origin_list:   # Loop over depots
        destination_list = mf.generate_destinations(Origin, afvoer_behoefte)   # List of possible destinations
        for Destination in destination_list:     # Loop over destinations
            # Obtain expected generated RC based on afvoerbehoeftevoorsp.
            df_afvoer = mf.generate_afvoer_df(Origin, Destination, afvoer_behoefte)
            # Obtain planned inter transports
            df_inter = mf.generate_inter_df(Origin, Destination, inter_transports)
            # Combine afvoer predictions and planned transports to predict number of RC on the depot floor
            df_stock = mf.generate_stock_prediction(df_afvoer, df_inter)
            # Save the stock prediction for this direction in a dict with the predictions for all directions
            stock_dict[(Origin, Destination)] = df_stock
            # Save the deficiency in transport (0 if sufficient transport)
            transport_deficiency.loc[Origin, Destination] = df_stock['stock'].iloc[-1]
            # Save the total surplus or deficiency in transport assuming all trucks are filled completely (negative if
            # there is more transport than RC produced)
            total_transport_diff.loc[Origin, Destination] = sum(df_stock['rc_forecast'])

    logger.info('Baseline computation - ended')

    # Below we write the results to an excel file
    baseline_path = config.PATH_AFVOER_BASELINE
    with pd.ExcelWriter(baseline_path) as writer:
        transport_deficiency.to_excel(writer, sheet_name='expected afvoertekort')
        total_transport_diff.to_excel(writer, sheet_name='total_transport_deficiency')
        for Origin in origin_list:
            destination_list = mf.generate_destinations(Origin, afvoer_behoefte)
            for Destination in destination_list:
                stock_dict[(Origin, Destination)].to_excel(writer, sheet_name=str(Origin) + '-' + str(Destination), index=False)
    logger.info('Baseline computation - results saved')

if __name__ == '__main__':
    main()
