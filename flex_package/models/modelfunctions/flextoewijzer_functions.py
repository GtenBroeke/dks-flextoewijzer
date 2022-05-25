import datetime as dt

import pandas as pd
import numpy as np

import PySources.Rijtijden.geocoderen as geocoderen
import PySources.Rijtijden.prepare_distance_time_matrices as prepare_distance_time_matrices
import PySources.ModelParams as mp
import itertools


class Truck:
    def __init__(self, name=None, location=None, destination=None, base=None, start=None, end=None, ext=None):
        self.Name = name
        self.Location = location
        self.Destination = destination
        self.Base = base
        self.Start = start
        self.End = end
        self.Load = 0
        self.Occupied = False
        self.Arrival = None
        self.LastArrival = None
        self.Returntime = None
        self.Location_list = [(location, start, "Start")]
        self.Active = False
        self.External = ext
        self.Blueflex = False
        self.Finished = False
        self.Orderlist = []
        self.CompletedOrders = []
        self.Moving_to_Pickup = False


class Depot:
    def __init__(self, name=None, afvoertekort=None):
        self.Name = name
        self.Afvoertekort = afvoertekort


class ReturnTrigger:
    def __init__(self, truck=None, time=None):
        self.Truck = truck
        self.Time = time


class ArrivalTrigger:
    def __init__(self, time=None, truck=None, location=None):
        self.Time = time
        self.Truck = truck
        self.Location = location


class StartShiftTrigger:
    def __init__(self, time=None, truck=None):
        self.Time = time
        self.Truck = truck


class Order:
    def __init__(self, time=None, a=None, b=None, c=None, d=None, origin=None, destination=None, flex=None):
        self.Time = time
        self.NprioA = a
        self.NprioB = b
        self.NprioC = c
        self.NprioD = d
        self.Ntot = a + b + c + d
        self.Origin = origin
        self.Destination = destination
        self.Solved = flex
        self.Call_time = time
        self.Combination = None
        self.Fulfilled = False
        self.PickupLoc = origin


        try:
            origin_type = mp.depot_info[mp.depot_info['Name'] == origin]['DepotType'].iloc[0]
        except:
            print("origin not found in depot info")
            origin_type = None
        try:
            destination_type = mp.depot_info[mp.depot_info['Name'] == destination]['DepotType'].iloc[0]
        except:
            print("destination not found in depot info")
            destination_type = None
        inter = 1
        if destination_type == 'CROSS':
            inter = 0
        if origin_type == 'DEPOT':
            inter = 0
        self.Inter = inter


def nearest_truck(location, trucks):
    """
    Function that computes which truck is closest to a location
    :param location: Location for which we compute which truck is closest
    :param trucks: List of trucks
    :return: The closest truck
    """
    min_time = dt.timedelta(hours=999999)
    closest_truck = None
    for truck in trucks:
        if not truck.Occupied:
            time = compute_travelling_time(truck.Location, location)
            if time < min_time:
                min_time = time
                closest_truck = truck
    return closest_truck


def compute_travelling_time(origin, destination):
    """
    Function to return the travelling time between two locations, using a matrix that contains all the travelling times
    :param origin: Starting location
    :param destination: Ending location
    :param drive_times: Matrix with drivetimes
    :return: The travelling time between the location
    """
    if origin == destination:
        travel_time = dt.timedelta(seconds=0)
    else:
        travel_time = mp.drive_times.loc[origin, destination]
    return travel_time


def select_truck(trucks, orders, time, force_solution=None):
    """
    Function that generates a list of all available trucks that could accept an order. The functions checks whether the
    truck would be back at its base in time after finishing the order. The function also considers trucks that are
    currently already completing an order, but might take the next order afterwards
    :param force_solution: If true, the selected truck will be forced to take the order, even if it will cause the
    truck to have a longer shift than planned
    :param trucks: List of trucks
    :param orders: List of orders (either 1 order or 2 combined orders with the same starting location)
    :param time: Current time
    :return: List of trucks that could finish the order in time
    """
    best_truck = None
    S = 0
    if force_solution == None:
        for truck in trucks:
            if truck.Finished:
                continue
            if truck.Blueflex and truck.Base != orders[0].Origin:
                continue
            start_time = get_order_starting_time(truck, time)
            route, travel_time = get_best_route(truck, orders)
            end_time = start_time + travel_time[-1] + mp.Loading_time + (len(orders) - 1) * 0.5 * mp.Loading_time
            loading_time = start_time + travel_time[1]
            prop_on_time = check_order_time(orders, loading_time)
            S_tot = compute_truck_efficiency(orders, time, start_time, travel_time[-1])*prop_on_time
            if end_time < truck.End and S_tot > S:
                best_time = travel_time
                best_truck = truck
                best_route = route
                S = S_tot
    else:
        best_truck = force_solution
        best_route, best_time = get_best_route(best_truck, orders)
    if best_truck is not None:
        best_truck = add_order_to_truck(best_truck, orders, time, best_time, best_route)
    return best_truck, S


def check_order_time(orders, end_time):
    """
    Return the proportion of rollcages in an order that is expected to be delivered on times
    :param orders: Order, or combination of orders
    :param end_time: Expected delivery time
    :return: Proportion expected to be on time
    """
    proportion_on_time_tot = 0
    N = 0
    origin = orders[0].Origin
    destination = orders[-1].Destination
    for order in orders:
        prios = [order.NprioA, order.NprioB, order.NprioC, order.NprioD]
        prop_on_time = proportion_on_time(origin, destination, prios, order.Inter, end_time)
        proportion_on_time_tot += order.Ntot * prop_on_time
        N += order.Ntot

    proportion_on_time_tot = proportion_on_time_tot / N
    return proportion_on_time_tot


def proportion_on_time(origin, destination, NRC_per_prio, inter, end_time):
    """

    :param origin: Origin of order to be fulfilled
    :param destination: Destination of order to be fulfilled
    :param NRC_per_prio: Number of rollcages for each prio
    :param inter: Type of transport, 0 for depot to crossdock, 1 for crossdock to fulfillment depot
    :param end_time: expected arrival time
    :return: expected proportion on time
    """
    prios = ('A', 'B', 'C', 'D')
    on_time = []
    for prio in prios:
        try:
            if inter == 0:
                final_departure_time = mp.final_departure_inter1[(origin, destination, prio)]
            else:
                final_departure_time = mp.final_departure_inter2[(origin, destination, prio)]
            if final_departure_time > end_time:
                on_time.append(1)
            else:
                on_time.append(0)
        except:
            "Prio combination not recognised"
            on_time.append(1)
    prop_on_time = sum(np.multiply(NRC_per_prio, on_time)) / sum(NRC_per_prio)
    return prop_on_time


def get_order_starting_time(truck, time):
    """
    Compute starting time for order fulfillment, based on current time and status of truck
    :param truck: Truck to fulfill order
    :param time: Current time
    :return: expected starting time
    """
    if truck.Active:
        if truck.LastArrival is not None:
            start_time = truck.LastArrival
        else:
            start_time = time
    else:
        start_time = truck.Start
    return start_time


def get_order_size(orders):
    """
    Get total number of rollcages for order, or combination of orders
    :param orders: List of orders
    :return: Total number of RC
    """
    NRC = 0
    for order in orders:
        NRC += order.Ntot
    return NRC


def assign_orders(trucks, unfulfilled_orders, time):
    """
    Assign orders to trucks
    :param trucks: List of available trucks
    :param unfulfilled_orders: List of orders to be fulfilled
    :param time: Current time
    :return: List of trucks (with assigned orders added to state of truck)
    """
    #perm = itertools.permutations(unfulfilled_orders)
    unfulfilled_orders_reverse = unfulfilled_orders.copy()
    unfulfilled_orders_reverse.reverse()
    perm = [unfulfilled_orders, unfulfilled_orders_reverse]
    optimal_efficiency = 0
    best_sequence = None
    for order_sequence in perm:
        trucks = free_unfulfilled_orders(trucks)
        efficiency = optimize_truck_assignment(trucks, order_sequence, time)
        if efficiency > optimal_efficiency:
            best_sequence = order_sequence
    if optimal_efficiency > 0:
        trucks = free_unfulfilled_orders(trucks)
        optimize_truck_assignment(trucks, best_sequence, time)
    return trucks


def free_unfulfilled_orders(trucks):
    """
    Remove planned orders from trucks that have not yet started the fulfillment of these orders
    :param trucks: List of trucks
    :return: Updated list of trucks
    """
    for truck in trucks:
        orderlist_old = truck.Orderlist.copy()
        truck.Orderlist = []
        for order in orderlist_old:
            if order[0].Fulfilled:
                truck.Orderlist.append(order)
        truck.LastArrival = truck.Arrival
    return trucks


def optimize_truck_assignment(trucks, order_sequence, time):
    """
    Find optimal assignment of trucks to sequence of orders
    :param trucks: List of trucks
    :param order_sequence: Sequence of trucks
    :param time: Current time
    :return: Criterion of optimization
    """
    S_tot = 0
    for order in order_sequence:
        truck, S_truck = select_truck(trucks, order, time)
        S_tot += S_truck
    return S_tot


def compute_truck_efficiency(orders, time, start_time, travel_time):
    """
    Compute optimization criterion for a single order, based on order size and travel time for fulfillment
    :param orders: Order to be fulfilled
    :param time: Current time
    :param start_time: Start time for fulfillment
    :param travel_time: Travel time required to fulfill order
    :return: Optimization criterion
    """
    NRC = get_order_size(orders)
    S_best = NRC / travel_time.seconds
    S_worst = NRC / (travel_time + (start_time - time)).seconds
    S_order = (mp.w1 * S_best + mp.w2 * S_worst)
    return S_order


def add_order_to_truck(truck, order, time, travel_time, route):
    """
    Add order to the list of orders to be fulfilled of a truck
    :param truck: Truck to fulfill order
    :param order: Order
    :param time: Current time
    :param travel_time: Required travel times
    :param destination: Order destination
    :return: truck, with updated state
    """

    truck.Orderlist.append(order)
    if truck.LastArrival is None:
        truck.LastArrival = time + travel_time[-1]
    else:
        truck.LastArrival += travel_time[-1]
    truck.Destination = route[-1]
    for ord in order:
        ord.PickupLoc = route[1]
    return truck


def travelling_time_trajectory(trajectory):
    """
    Compute total travelling time for a trajectory (i.e.,sequence of locations)
    :param trajectory: Sequence of locations
    :return: Total travelling time
    """
    total_time = [dt.timedelta(hours=0)]
    for start, end in zip(trajectory, trajectory[1:]):
        total_time.append(total_time[-1] + compute_travelling_time(start, end))
    return total_time


def get_start_location(name):
    """
    Function that extracts the starting location for each truck from the registration documents.
    :param name: Name that is in the registration document
    :return: Location
    """
    name = name.strip()
    if name == 'EXT WW':
        name = 'XWW'
    if name == 'EX WW':
        name = 'XWW'
    location = name.split(" ")[0]
    location = ''.join([i for i in location if not i.isdigit()])
    location = location.upper()
    name = name.upper()
    if location == 'ALP':
        location = 'ALR'
    if location == 'NWG':
        location = 'NIWG'
    if location == 'VILV':
        location = 'VIL'
    if location == 'ELST':
        location = 'ELT'
    if location == 'EXW':
        location = 'XWW'
    if location == 'BOL':
        location = 'BFC'
    if name == 'BFC ':
        location = 'BFC'
    if name == 'BOL 2':
        location = 'TB'
    if name == 'BOL.COM':
        location = 'TB'
    if location == 'BOL.COM':
        location = 'TB'
    if location == 'WW':
        location = 'XWW'
    if name == 'BLUE ALR':
        location = 'ALR'
    if name == 'BLUEFL ALR':
        location = 'ALR'
    if name == 'BLUE ALM':
        location = 'ALR'
    if name == 'BLUEFL TB':
        location = 'TB'
    if name == 'FLEX ALR':
        location = 'ALR'
    if name == 'BOLVW':
        location = 'HT'
    if name == 'BLUE FLEX ALR':
        location = 'ALR'
    if name == 'BLUE FLEX TB':
        location = 'TB'
    if name == 'BLUE TB':
        location = 'TB'
    if location == 'EXWW':
        location = 'XWW'
    if location == 'ZMB':
        location = 'ZBM'
    if location == 'EXTWW':
        location = 'XWW'
    if name == 'FLEX EXT WW':
        location = 'XWW'
    if location == 'EXT':
        location = 'XWW'
    if location == 'XSAD':
        location = 'XASD'
    if location == 'WMG':
        location = 'WML'
    if location == 'WVWN':
        location = 'WVN'
    if location == 'ZWO':
        location = 'ZL'
    if location == 'EX WW':
        location = 'XWW'
    if location == 'ZWD':
        location = 'ZL'
    if name == 'FLEX WMG':
        location = 'WML'
    if name == 'NWG EMB A':
        location = 'NIWG'
    if name == 'FLEX BOL':
        location = 'BFC'
    if name == 'FLEX BOL 2':
        location = 'BFC'
    if location == 'FLEX':
        location = 'BFC'
    if location == 'FLEX':
        location = 'ASD ZO'
    if name == 'FLEX BOL 1':
        location = 'BFC'
    if name == 'FLEX BFC':
        location = 'TB'
    if name == 'BLUEFLEX ALR':
        location = 'ALR'
    if name == 'BLUEFLEX TB':
        location = 'TB'
    if name == 'BLUEFLEX TB':
        location = 'TB'
    if name == 'BLEUFLEX TB':
        location = 'TB'
    return location


def fulfill_order(order, truck, time):
    """
    Function that carries out the operations needed for a truck to fulfill an order, updates the status of the truck,
    and computes when the truck is expected to become available again. The function considers when currently occupied
    trucks are expected to become available
    :param trajectory: sequence of locations for the order to be fulfilled
    :param order: Order to be fulfilled
    :param truck: Truck that will fulfill the order
    :param time: Current time
    :param loading_unloading_time: Time needed to load and unload
    :param drive_times: drive times between all locations
    :return: An arrival trigger that tracks the return of the truck after fulfillment
    """
    truck.Occupied = True
    truck.Load = get_order_size(order)
    trajectory, travel_time = get_best_route(truck, order)
    truck.Destination = trajectory[-1]
    arrival_time = time
    action = "Load"
    loc = truck.Location
    for location in trajectory[1:-1]:
        arrival_time += compute_travelling_time(loc, location)
        for o in order:
            if location == o.Destination:
                action = "Unload"
        truck.Location_list.append((location, arrival_time, action))
        arrival_time += 0.5 * mp.Loading_time
        loc = location
    truck.Arrival = arrival_time
#    if truck.LastArrival is None:
#        truck.LastArrival = arrival_time
    arrival = ArrivalTrigger(arrival_time, truck, truck.Destination)
    return arrival


def start_order_fulfillment(truck, event_list, time, fulfilled_orders, unfulfilled_orders):
    """
    Start fullfilment of an order
    :param truck: Truck to fulfill order
    :param event_list: List of all (future) events
    :param time: Current time
    :param fulfilled_orders: List of fulfilled orders
    :param unfulfilled_orders: List of unfulfilled orders
    :return: Updated truck, event_list, fulfilled_orders list, and unfulfilled_orders list
    """
    order = truck.Orderlist[0]
    truck.Orderlist.pop(0)
    truck.CompletedOrders.append(order)
    if truck.Blueflex:
        truck.Blueflex = False
    order = set_order_to_fulfilled(order, truck.Name)
    Arrival = fulfill_order(order, truck, time)
    # Remove previous return trigger (trigger for truck to return to base) and arrival trigger from list of
    # events. These are to be replaced, now that the route of the truck was altered
    event_list = remove_return_trigger(event_list, truck)
    event_list = remove_arrival_trigger(event_list, truck)
    event_list.append(Arrival)  # Add new arrival trigger
    event_list = sorted(event_list, key=lambda x: x.Time)  # Sort updated event list by time
    # Update list of fulfilled orders
    (fulfilled_orders, unfulfilled_orders) = update_order_list(order, fulfilled_orders, unfulfilled_orders)
    return truck, event_list, fulfilled_orders, unfulfilled_orders


def set_order_to_fulfilled(order, truckname):
    """
    Update status of order that is being fulfilled
    :param order: Order that is fulfilled
    :param truckname: Name of the truck executing the fulfillment
    :return:
    """
    for suborder in order:
        suborder.Fulfilled = True
        suborder.Solved = truckname
    return order


def get_best_route(truck, order):
    """
    Compute travelling time for truck to fulfill order, and find optimal route
    :param truck: Truck to fulfill order
    :param order: Order to be fulfilled
    :return: Optimal route, and corresponding travelling time
    """
    if truck.Arrival is not None:
        start_location = truck.Destination
    else:
        start_location = truck.Location
    if len(order) == 1:
        routes = [[start_location, order[0].Origin, order[0].Destination, truck.Base]]
    elif len(order) == 2 and order[0].Origin == order[1].Origin:
        routes = [[start_location, order[0].Origin, order[0].Destination, order[1].Destination, truck.Base],
                  [start_location, order[0].Origin, order[1].Destination, order[0].Destination, truck.Base]]
    else:
        routes = [[start_location, order[0].Origin, order[1].Origin, order[1].Destination, truck.Base],
                  [start_location, order[1].Origin, order[0].Origin, order[0].Destination, truck.Base]]
    travel_time_min = dt.timedelta(hours=24)
    best_route = None
    best_travel_time = None
    for route in routes:
        travel_time = travelling_time_trajectory(route)
        if travel_time[-1] < travel_time_min:
            travel_time_min = travel_time[-1]
            best_route = route
            best_travel_time = travel_time
    if best_route is not None:
        return best_route, best_travel_time
    else:
        return None, None


def move_to_pickup_loc(truck, event_list, time):
    truck.Moving_to_Pickup = True
    event_list = remove_return_trigger(event_list, truck)
    event_list = remove_arrival_trigger(event_list, truck)
    arrival_time = time + mp.drive_times.loc[truck.Location, truck.Orderlist[0][0].PickupLoc]
    arrival = ArrivalTrigger(arrival_time, truck, truck.Orderlist[0][0].PickupLoc)
    event_list.append(arrival)  # Add new arrival trigger
    event_list = sorted(event_list, key=lambda x: x.Time)  # Sort updated event list by time
    return truck, event_list


def remove_return_trigger(event_list, truck):
    """
    Function to remove the trigger for a truck to return to its base from the event list
    :param event_list: List of (chronological) events
    :param truck: Truck for which the trigger is to be removed
    :return: New version of the event list
    """
    for event in list(event_list):
        if isinstance(event, ReturnTrigger):
            if event.Truck == truck:
                event_list.remove(event)
    return event_list


def remove_arrival_trigger(event_list, truck):
    """
    Function that removes the trigger for a truck to arrive at its destination from the event list. This function is
    called when a truck gets a new destination
    :param event_list: List of (chronological) events
    :param truck: Truck for which the trigger is to be removed
    :return: New version of the list of events
    """
    for event in list(event_list):
        if isinstance(event, ArrivalTrigger):
            if event.Truck == truck:
                event_list.remove(event)
    return event_list


def make_available(truck):
    """
    Function to make a truck available again after finishing an order. The function also creates a trigger for the truck
    to return to base in time
    :param truck:
    :return: Trigger for the truck to return to base from its present location
    """
    #truck.Location = truck.Destination
    truck.Destination = None
    truck.Arrival = None
    truck.Occupied = False
    truck.Load = 0

    return_time = compute_travelling_time(truck.Location, truck.Base)
    return_time = truck.End - return_time
    return_event = ReturnTrigger(truck, return_time)
    return return_event


def start_shift(truck):
    """
    Function that updates the status of a truck when it starts its shift
    :param truck:
    """
    truck.Occupied = False
    truck.Active = True


def return_to_base(truck, time):
    """
    Function that makes a truck return to base, ending its shift
    :param truck: The truck to return to base
    :param time: Present time
    """
    travel_time = compute_travelling_time(truck.Location, truck.Base)
    return_time = time + travel_time
    truck.Location = truck.Base
    truck.Occupied = True
    truck.Location_list.append((truck.Location, return_time, "return to base"))
    truck.Active = False
    truck.Finished = True


def check_unfulfilled_orders(truck, orderlist, time):
    """
    Function that lets a truck check if any orders are available. This function is called when the truck becomes
    available after starting its shift or finishing an order
    :param truck: Truck looking for a new order
    :param orderlist: List of open orders
    :param time: Present time
    :param loading_unloading_time: Time needed for the truck to load and unload a single order
    :return: The order closest to the truck's present location
    """
    min_travel_time = dt.timedelta(hours=24)
    closest_order = None
    base_time = compute_travelling_time(truck.Location, truck.Base)
    for order in orderlist:
        travel_time = compute_travelling_time(truck.Location, order.Origin)
        return_time = compute_travelling_time(order.Destination, truck.Base)
        fulfillment_time = mp.Loading_time + compute_travelling_time(order.Origin, order.Destination)
        total_time = time + travel_time + return_time + fulfillment_time
        if total_time < truck.End:
            extra_time = travel_time + fulfillment_time + return_time - base_time
            if extra_time < min_travel_time:
                min_travel_time = extra_time
                closest_order = order
    return closest_order


def clean_orders(tekorten):
    """
    Function to clean data with orders from the registration documents
    :param tekorten: Input data from registration document
    :return: Cleaned data
    """
    tekorten = tekorten[tekorten['Tijd'].notnull()]
    tekorten = tekorten[tekorten['Totaal'] > 0]
    tekorten = tekorten.dropna(subset=['Van', 'Naar'])
    tekorten = tekorten[tekorten['Van'].str.contains('SCB')==False]
    tekorten = tekorten[tekorten['Naar'].str.contains('SCB')==False]
    tekorten = tekorten[tekorten['Van'].str.contains('ECS')==False]
    tekorten = tekorten[tekorten['Naar'].str.contains('ECS')==False]
    tekorten = tekorten[tekorten['Naar'] != 'FR']
    pd.options.mode.chained_assignment = None
    tekorten['Tijd'] = tekorten['Tijd'].apply(lambda x: x.replace("u", ":") if type(x) == str else x)
    tekorten['Tijd'] = tekorten['Tijd'].apply(lambda x: x.replace("U", ":") if type(x) == str else x)
    tekorten['Tijd'] = tekorten['Tijd'].apply(
        lambda x: dt.datetime.strptime(x, "%H:%M").time() if type(x) == str else x
    )
    pd.options.mode.chained_assignment = "warn"
    pd.options.mode.chained_assignment = None
    tekorten['Van'] = tekorten['Van'].apply(lambda x: x.strip())
    tekorten['Naar'] = tekorten['Naar'].apply(lambda x: x.strip())
    tekorten['Van'] = tekorten['Van'].apply(lambda x: x.upper())
    tekorten['Naar'] = tekorten['Naar'].apply(lambda x: x.upper())
    tekorten.replace(['TIEL'], ['TL'], inplace=True)
    tekorten.replace(['ALP'], ['ALR'], inplace=True)
    tekorten.replace(['NWG'], ['NIWG'], inplace=True)
    tekorten.replace(['ZMB'], ['ZBM'], inplace=True)
    tekorten.replace(['WVWN'], ['WVN'], inplace=True)
    tekorten.replace(['XSAD'], ['XASD'], inplace=True)
    tekorten.replace(['XTL'], ['TL'], inplace=True)
    tekorten.replace(['TL '], ['TL'], inplace=True)
    tekorten.replace(['ELST'], ['ELT'], inplace=True)
    tekorten.replace(['EXTWW'], ['XWW'], inplace=True)
    tekorten.replace(['WW'], ['XWW'], inplace=True)
    tekorten.replace(['Ex WW'], ['XWW'], inplace=True)
    tekorten.replace(['ASDZO'], ['ASD'], inplace=True)
    tekorten.replace(['ASD ZO'], ['ASD'], inplace=True)
    tekorten.replace(['ASZO'], ['ASD'], inplace=True)
    tekorten.replace(['SNI (BE)'], ['SNI'], inplace=True)
    tekorten.replace(['OEV (BE)'], ['OEV'], inplace=True)
    tekorten.replace(['OEVEL'], ['OEV'], inplace=True)
    tekorten.replace(['VIL (BE)'], ['VIL'], inplace=True)
    tekorten.replace(['VILV'], ['VIL'], inplace=True)
    tekorten.replace(['DTD (BE)'], ['DTD'], inplace=True)
    tekorten.replace(['WMG'], ['WML'], inplace=True)
    tekorten.replace(['WML (BE)'], ['WML'], inplace=True)
    tekorten.replace(['ARD (BE)'], ['ARD'], inplace=True)
    tekorten.replace(['NAM (BE)'], ['NAM'], inplace=True)
    tekorten.replace(['STT (BE)'], ['STT'], inplace=True)
    tekorten.replace(['TEM'], ['NAM'], inplace=True)    ### Deze nog vervangen..
    tekorten.replace(['TEM (BE)'], ['NAM'], inplace=True)
    tekorten.replace(['STN'], ['STT'], inplace=True)
    tekorten.replace(['WB (BE)'], ['WB'], inplace=True)
    tekorten.replace(['ZWO'], ['ZL'], inplace=True)
    tekorten.replace(['ZWD'], ['ZL'], inplace=True)
    tekorten.replace(['EXT WW'], ['XWW'], inplace=True)
    tekorten.replace(['EX WW'], ['XWW'], inplace=True)
    tekorten.replace(['SKP NMG'], ['SKP'], inplace=True)
    tekorten.replace(['SKP NMG '], ['SKP'], inplace=True)
    tekorten.replace(['SKP '], ['SKP'], inplace=True)
    tekorten.replace(['BFC '], ['BFC'], inplace=True)
    tekorten.replace(['WMG'], ['WML'], inplace=True)
    tekorten = tekorten[tekorten['Naar'] != tekorten['Van']]
    pd.options.mode.chained_assignment = "warn"
  #  tekorten['A'] = tekorten['A'].apply(lambda x: x if type(x) == int else 0)
  #  tekorten['B'] = tekorten['B'].apply(lambda x: x if type(x) == int else 0)
  #  tekorten['C'] = tekorten['C'].apply(lambda x: x if type(x) == int else 0)
  #  tekorten['D'] = tekorten['D'].apply(lambda x: x if type(x) == int else 0)
  #  tekorten['BE'] = tekorten['BE'].apply(lambda x: x if type(x) == int else 0)
    tekorten['Tijd'] = tekorten['Tijd'].apply(lambda x: x.time() if type(x) == dt.datetime else x)
    return tekorten


def combine_orders(order, event_list, unfulfilled_orders):
    """
    Check if the present order can be combined with any other orders that were called in at the same time, or are still
    unresolved
    :param order: Present order
    :param event_list: List of upcoming events (to check if there are any orders called in at the same time)
    :param unfulfilled_orders: List of previous orders that are not yet completed
    :return: List of combined orders (may consist of only the present order, or include an additional order
    """
    for cord in event_list:
        if cord.Time <= order.Time and isinstance(cord, Order):
            order, cord = check_combination(order, cord)
            if order.Combination == cord:
                event_list.remove(cord)
                return [order, cord], event_list, unfulfilled_orders

    for cord in unfulfilled_orders:
        if len(cord) == 1:
            order, cord[0] = check_combination(order, cord[0])
            if order.Combination == cord[0]:
                unfulfilled_orders.remove(cord)
                return [order, cord[0]], event_list, unfulfilled_orders

    return [order], event_list, unfulfilled_orders


def check_combination(order1, order2):
    """
    Check whether two orders can be combined. If the combination is possible, a link to one order is stored in the state
    of the other order, and vice versa.
    :param order1: First order
    :param order2: Second order
    :return: Both orders
    """
    if order1.Ntot + order2.Ntot <= mp.truck_cap:
        if order1.Origin == order2.Origin or order1.Destination == order2.Destination:
            order1.Combination = order2
            order2.Combination = order1
    return order1, order2


def add_date(tekorten, day):
    """
    Add date to the afvoertekorten read from the registration document (field contains only time)
    :param tekorten: List of afvoertekorten read from the registration document
    :param day: Process day
    :return: List of afvoertekorten, including added dates
    """
    next_day = 0
    for ind, row in tekorten.iterrows():
        time = row['Tijd']
        if time < dt.time(4, 00) and next_day == 0:
            day = day + dt.timedelta(days=1)
            next_day = 1
        tekorten.at[ind, 'Tijd'] = dt.datetime.combine(day, row['Tijd'])
    return tekorten


def read_flex(registratie_path, day):
    """
    Function that reads the available flex trucks from the registration maintained by Control Room. Some data cleaning
    is performed, and a list of Trucks is initialised.
    :param registratie_path: Path to the registration document
    :return: List of initialised trucks.
    """
    try:
        df = pd.read_excel(registratie_path, sheet_name='Flex')
    except:
        df = pd.read_excel(registratie_path, sheet_name='Flex Nieuw')

    df.rename(columns={"Unnamed: 2": "TStart", "Unnamed: 3": "TEnd"}, inplace=True)
    df.rename(columns={"Start": "TStart", "Eind": "TEnd"}, inplace=True)

    df['TStart'] = df['TStart'].apply(lambda x: x.replace('u', ':') if type(x) == str else x)
    df['TStart'] = df['TStart'].apply(lambda x: x.replace('U', ':') if type(x) == str else x)
    df['TStart'] = df['TStart'].apply(lambda x: dt.datetime.strptime(x, "%H:%M").time() if (type(x) == str and len(x) == 5) else x)
    df['TStart'] = df['TStart'].apply(lambda x: dt.datetime.strptime(x, "%H:%M:%S").time() if (type(x) == str and len(x) == 8) else x)
    df['TStart'] = df['TStart'].apply(lambda x: x if type(x) == dt.time else np.nan)
    df = df.dropna(subset=['TStart'])

    df['TEnd'] = df['TEnd'].apply(lambda x: x.replace('u', ':') if type(x) == str else x)
    df['TEnd'] = df['TEnd'].apply(lambda x: x.replace('U', ':') if type(x) == str else x)
    df['TEnd'] = df['TEnd'].apply(lambda x: dt.datetime.strptime(x, "%H:%M").time() if (type(x) == str and len(x) == 5) else x)
    df['TEnd'] = df['TEnd'].apply(lambda x: dt.datetime.strptime(x, "%H:%M:%S").time() if (type(x) == str and len(x) == 8) else x)
    df['TEnd'] = df['TEnd'].apply(lambda x: x if type(x) == dt.time else np.nan)
    df = df.dropna(subset=['TEnd'])
    df = df.reset_index(drop=True)

    start_day = day
    df['StartDay'] = start_day
    for ind, row in df.iterrows():
        if type(row['TStart']) == dt.time:
            if row['TStart'] < dt.time(hour=6):
                start_day = day + dt.timedelta(hours=24)
            df['StartDay'].iloc[ind] = start_day
    df = df.dropna(subset=['Flex ', 'TStart', 'TEnd'])
    df['EndDay'] = df.apply(lambda x: x.StartDay if x.TEnd > x.TStart else day + dt.timedelta(hours=24), axis=1)

    df['Flex '] = df['Flex '].apply(lambda x: x.upper())

    if 'Laden' in df.columns:
        df['Laden'] = df['Laden'].apply(lambda x: x.upper() if type(x) == str else x)
        df = df.drop(df[df['Laden'].str.contains('UITGELEEND') == True].index)
    if 'Leeg' in df.columns:
        df['Leeg'] = df['Leeg'].astype(str)
        df['Leeg'] = df['Leeg'].apply(lambda x: x.upper() if type(x) == str else x)
        df = df.drop(df[df['Leeg'].str.contains('UITGELEEND') == True].index)


    df['ShiftStart'] = df.apply(lambda x: dt.datetime.combine(x.StartDay, x.TStart), axis=1)
    df['ShiftEnd'] = df.apply(lambda x: dt.datetime.combine(x.EndDay, x.TEnd), axis=1)

    df['External'] = df['Wagencode '].apply(lambda x: False if len(str(x)) == 3 else True)

    trucks = generate_trucks(df)

    return trucks


def generate_trucks(df):
    """
    Function to initialize trucks that are available for the day, using input data from the registration documents
    maintained by control room
    :param df: dataframe based on registration document
    :param start_day: date at the start of the process
    :return: list of available trucks, including initital state for each truck
    """
    truck_list = []
    for ind, row in df.iterrows():
        startloc = get_start_location(row['Flex '])
        name = row['Flex '].replace(" ", "")
        truck = Truck(name=name, location=startloc, start=row['ShiftStart'], end=row['ShiftEnd'], base=startloc, ext=row['External'])
        if 'BLUE' in truck.Name or 'BOL' in truck.Name:
            truck.Blueflex = True
        truck_list.append(truck)
    return truck_list


def read_tekorten(registratie_path, day):
    """
    Function to read afvoertekorten, either from a file generated based on afvoerpredictions, or from the registration
    maintained by control room.
    :param registratie_path:
    :return: Dataframe containing afvoertekorten
    """
    if mp.Afvoer_predictions:
        Tekorten = pd.read_excel("generated_orders.xlsx", sheet_name='orders')
    else:
        Tekorten = pd.read_excel(registratie_path, sheet_name='Afvoertekorten')
        Tekorten = clean_orders(Tekorten)
        Tekorten = add_date(Tekorten, day)
    return Tekorten


def generate_event_list(tekorten, truck_list):
    """
    Function to generate an initial list with events read in from the registration document
    :param tekorten: Afvoertekorten, as read from registration document
    :param truck_list: List of trucks, taken from registration document
    :return: list of events
    """
    event_list = []
    tekorten.fillna({'A': 0, 'B': 0, 'C': 0, 'D': 0, 'BE': 0}, inplace=True)

    tekorten['Oplossing'] = tekorten.apply(lambda x: x.Oplossing.upper() if x.Status == 'Opgelost' and type(x.Oplossing) == str else None, axis=1)
    tekorten['Oplossing'] = tekorten['Oplossing'].apply(lambda x: x if x is None else x.replace('FLEX', '').replace(' ', ''))
    for ind, row in tekorten.iterrows():
        event_list.append(
            (Order(time=row['Tijd'], a=row['A'] + row['BE'], b=row['B'], c=row['C'], d=row['D'], origin=row['Van'],
                   destination=row['Naar'], flex=row['Oplossing'])))

    for truck in truck_list:
        time = truck.Start
        event_list.append(StartShiftTrigger(time=time, truck=truck))
        return_time = compute_travelling_time(truck.Location, truck.Base)
        return_time = truck.End - return_time
        return_event = ReturnTrigger(truck, return_time)
        event_list.append(return_event)
    event_list = sorted(event_list, key=lambda x: x.Time)
    return event_list


def update_order_list(combination_list, fulfilled_orders, unfulfilled_orders):
    """
    Function to update order list, after an order has been fulfilled
    :param combination_list: List of completed order(s)
    :param fulfilled_orders: List of fulfilled orders (to be updated)
    :param unfulfilled_orders: List of fulfilled orders (to be updated)
    :return: Updated lists of fulfilled and unfulfilled orders
    """
    fulfilled_orders.append(combination_list)
    try:
        unfulfilled_orders.remove(combination_list)
    except:
        print("Finished order already removed from unfulfilled orderlist")
    return fulfilled_orders, unfulfilled_orders


def remove_fulfilled_orders(event_list, combination_list):
    """
    Remove fulfulled from the list of events
    :param event_list: List of (future) events
    :param combination_list: list of completed orders
    :return: updated list of events
    """
    for event in event_list:
        if event[1] in combination_list:
            event_list.remove(event)
    return event_list


def check_shift_extension(trucks, orders, time):
    """
    Function that generates a list of all external trucks that could accept an order if the shift were extended.
    :param trucks: List of trucks
    :param orders: List of orders (either 1 order or 2 combined orders with the same starting location)
    :param time: Current time
    :return: List of trucks that could finish the order in time
    """
    available_trucks = []
    if len(orders) == 1:
        for truck in trucks:
            if truck.Active and truck.External:
                if truck.Arrival is not None:
                    start_time = truck.Arrival
                else:
                    start_time = time

                travel_time_pickup = compute_travelling_time(truck.Location, orders[0].Origin)
                travel_time_delivery = compute_travelling_time(orders[0].Origin, orders[0].Destination)
                travel_time_return = compute_travelling_time(orders[0].Destination, truck.Base)
                end_time = start_time + travel_time_pickup + travel_time_delivery + travel_time_return + \
                    mp.Loading_time
                if end_time < (truck.End + mp.shift_extension):
                    available_trucks.append(truck)
    if len(orders) == 2:
        for truck in trucks:
            if truck.Active and truck.External:
                if truck.Arrival is not None:
                    start_time = truck.Arrival
                else:
                    start_time = time

                travel_time_pickup = compute_travelling_time(truck.Location, orders[0].Origin)
                travel_time_delivery1 = compute_travelling_time(orders[0].Origin, orders[0].Destination)
                travel_time_delivery2 = compute_travelling_time(orders[0].Origin, orders[1].Destination)
                if travel_time_delivery1 < travel_time_delivery2:
                    travel_time_delivery_tot = travel_time_delivery1 + \
                                               compute_travelling_time(
                                                   orders[0].Destination, orders[1].Destination
                                               )
                    travel_time_return = compute_travelling_time(orders[1].Destination, truck.Base)
                else:
                    travel_time_delivery_tot = travel_time_delivery1 + \
                                               compute_travelling_time(
                                                   orders[1].Destination, orders[0].Destination
                                               )
                    travel_time_return = compute_travelling_time(orders[0].Destination, truck.Base)
                end_time = start_time + travel_time_pickup + travel_time_delivery_tot + \
                    travel_time_return + mp.Loading_time * 1.5
                if end_time < (truck.End + mp.shift_extension):
                    available_trucks.append(truck)
    return available_trucks


def compute_drive_times(path):
    df = pd.read_csv(path, sep=';')

    for i in df.index:
        lat, lon = geocoderen.geocoderen(df.loc[i, "Straat"],
                                         df.loc[i, "Huisnummer"],
                                         df.loc[i, "Postcode"],
                                         df.loc[i, "Plaats"],
                                         df.loc[i, "Land"])
        df.loc[i, "lat"] = lat
        df.loc[i, "lon"] = lon
    afk = df['Afk']

    df = prepare_distance_time_matrices.add_AdresID(df)

    df = df[["AdresID", "lat", "lon"]]
    df_distances, df_durations = prepare_distance_time_matrices.times_distances_from_scratch(df)

    df_durations = df_durations / 60
    df_durations.columns = afk
    df_durations.index = afk
    df_durations = df_durations.applymap(format_drive_times)
    return df_durations


def format_drive_times(decimal_time):
    """
    Convert drivetimes from a decimal number to datetime.tim
    :param decimal_time: time expressed as decimal number
    :return: time expressed as datetime.timedelta object
    """
    minutes = int(decimal_time)
    seconds = (decimal_time % 1) * 60
    output = dt.timedelta(minutes=minutes, seconds=seconds)
    return output
