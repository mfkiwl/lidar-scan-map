"""Collection of car operation commands
"""

import pickle
import time
import map_scan_data
import omnicar

car = omnicar.OmniCar()

PAUSE = 0.05  # sec PAUSE time needed between wheel motor commands
MIN_LENGTH = 20  # threshold min length to end of wall
MIN_DIST = 40  # threshold min distance from car to wall
KP = 0.5  # steering proportional PID coefficient
KD = 0.6  # steering derivative PID coefficient
SPD = 100  # default car speed

def jog_FR(spd, t, trim=5):
    """Jog diagonally forward + right at spd (int 0-255) for t seconds
    """
    car.go_FR(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_FL(spd, t, trim=5):
    """Jog diagonally forward + left at spd (int 0-255) for t seconds
    """
    car.go_FL(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_BL(spd, t, trim=5):
    """Jog diagonally back + left at spd (int 0-255) for t seconds
    """
    car.go_BL(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_BR(spd, t, trim=5):
    """Jog diagonally back + right at spd (int 0-255) for t seconds
    """
    car.go_BR(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_F(spd, t, trim=5):
    """Jog forward at spd (int: 100-255) for t seconds
    trim (int) is used to null out any unwanted spin.
    """
    car.go_F(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_B(spd, t, trim=5):
    """Jog backward at spd (int: 100-255) for t seconds
    trim (int) is used to null out any unwanted spin.
    """
    car.go_B(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_L(spd, t, trim=5):
    """Jog left at spd (int: 100-255) for t seconds
    trim (int) is used to null out any unwanted spin.
    """
    car.go_L(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_R(spd, t, trim=7):
    """Jog right at spd (int: 100-255) for t seconds
    trim (int) is used to null out any unwanted spin.
    """
    car.go_R(spd, trim)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_cw(spd, t):
    """Spin car CW at spd (int between 100-255) for t seconds
    """
    car.spin_cw(spd)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def jog_ccw(spd, t):
    """Spin car CCW at spd (int between 100-255) for t seconds
    """
    car.spin_ccw(spd)
    time.sleep(t)
    car.stop_wheels()
    time.sleep(PAUSE)

def scan_series(nbr, lev=10000, hev=30000):
    """Perform a series of nbr successive scans of angular sector from
    lev (low encoder value) to hev (high encoder value), moving the car
    between scans. Save the raw scan data as a pickle file.
    Generate & save map plots.
    """
    data_list = []  # list of scan data from multiple scans
    while nbr:
        scan_data = car.scan(low_enc_val=lev, hi_enc_val=hev)
        print(scan_data[0])
        print("Number of data points: ", len(scan_data))
        scan_data.pop(0)  # may have 'stale' serial data
        print(scan_data[0])
        print("Number of data points: ", len(scan_data))
        data_list.append(scan_data)
        nbr -= 1
        if nbr:
            time.sleep(PAUSE)
            # Move the car between successive scans
            # jog_R(100, 0.75)
            jog_F(100, 1.0, trim=5)

    # Save scan data for later examination, if desired.
    with open('scan_data.pkl', 'wb') as f:
        pickle.dump(data_list, f)

    # map the scans
    for n, scan_data in enumerate(data_list):
        print()
        print(f"Scan number {n+1} of {len(data_list)}")
        map_scan_data.show_map(scan_data, n+1)

def remap_scans():
    """Load saved scan data and generate maps.
    """
    modes = ('straight', 'corner')
    for mode in modes:
        if mode == 'straight':
            data_file = 'scan_data.pkl'
            map_folder = 'sideMaps'
        elif mode == 'corner':
            data_file = 'corner_data.pkl'
            map_folder = 'cornerMaps'
        with open(data_file, 'rb') as f:
            data_list = pickle.load(f)

        for n, scan_data in enumerate(data_list):
            print()
            print(f"Scan number {n+1} of {len(data_list)}")
            map_scan_data.show_map(scan_data, map_folder, n+1)

def drive_and_scan(spd=SPD):
    """
    Drive parallel to wall on left keeping track of its parameters:
        length: distance from projection of car to the end of wall.
        angle: angle of the wall w/r/t car's X axis. target = 90 degrees
        x_dist: lateral distance to the wall (in x direction)
    Start out initially so that x_dist >= MIN_DIST
    Stop the car when the value of length drops below MIN_LENGTH.
    While driving, adjust steering trim to minimize angle error.
    """
    data_list = []  # list of data from multiple scans

    # Before driving along wall, move the car sideways until it is
    # at least the minimum desired distance from the wall at left.
    scan_data = car.scan(low_enc_val=10000, hi_enc_val=20000)
    data_list.append(scan_data)
    start_idx, end_idx, length, angle, x_dist = map_scan_data.analyze_data(scan_data)
    threshold_idx = (start_idx + end_idx) / 2
    print(f"length: {length}")
    print(f"angle: {angle}")
    print(f"x_dist: {x_dist}")
    print()
    if abs(x_dist) < MIN_DIST:  # too close to wall
        car.go_R(spd)
        time.sleep(PAUSE)
        print("Driving away from wall")
        print()
        while abs(x_dist) < MIN_DIST:  # move farther from wall
            scan_data = car.scan(low_enc_val=10000, hi_enc_val=20000)
            data_list.append(scan_data)
            start_idx, end_idx, length, angle, x_dist = map_scan_data.analyze_data(scan_data)
            threshold_idx = (start_idx + end_idx) / 2
            print(f"length: {length}")
            print(f"angle: {angle}")
            print(f"x_dist: {x_dist}")
            print()

    car.stop_wheels()
    print("Wheels Stopped")
    print()

    # Set up to drive parallel to wall (wall angle should be 90 degrees)
    turn(angle - 90)
    steer_target = car.heading()
    print(f"target heading = {steer_target}")
    prev_error = 0

    trim = 3  # estimate of correct steering trim
    time.sleep(PAUSE)
    if length > MIN_LENGTH:  # drive along wall
        car.go_F(spd, trim=trim)
        time.sleep(PAUSE)
        print("Driving along wall")
        print()
    while length > MIN_LENGTH:  # continue while steering
        scan_data = car.scan(low_enc_val=10000, hi_enc_val=20000)
        data_list.append(scan_data)
        start_idx, end_idx, length, angle, x_dist = map_scan_data.analyze_data(scan_data)
        if start_idx > threshold_idx:
            print("Left wall gone from view: Exiting loop")
            break
        threshold_idx = (start_idx + end_idx) / 2
        print(f"length: {length}")
        print(f"angle: {angle}")
        print(f"x_dist: {x_dist}")
        heading = car.heading()
        print(f"heading: {heading}")
        print()
        # Adjust trim to keep car heading matched to steer_target
        # Use pid feedback loop
        error = heading - steer_target
        p_term = error
        d_term = error - prev_error
        prev_error = error
        adjustment = int((p_term * KP + d_term * KD))
        trim += adjustment
        print(f"p_term = {p_term}, d_term = {d_term}, trim = {trim}")
        car.go_F(spd, trim=trim)
    car.stop_wheels()
    time.sleep(PAUSE)
    print("Wheels Stopped")
    print()
    # Save collected scan data
    # Use remap_scans() to map it.
    with open('scan_data.pkl', 'wb') as f:
        pickle.dump(data_list, f)

def cross_corner_scan(spd=SPD):
    """
    Traverse corner from the end of one wall to the start of the next:
        drive forward while scanning
        watch for angle to flip from 45 (old wall) to 135 (new wall)
        then keep going a little farther
    """
    data_list = []  # list of data from multiple scans

    scan_data = car.scan(low_enc_val=10000, hi_enc_val=20000)
    data_list.append(scan_data)
    strt_idx, end_idx, length, angle, x_dist = map_scan_data.analyze_data(scan_data)
    print(f"length: {length}")
    print(f"angle: {angle}")
    print(f"x_dist: {x_dist}")
    print()
    car.go_F(spd, trim=7)
    time.sleep(PAUSE)
    print("Driving across corner")
    print()
    xtra_loops = 2  # number of extra times to go through loop below
    more = 0  # flag to go through loop below more times
    while angle < 90 or more < xtra_loops:
        scan_data = car.scan(low_enc_val=10000, hi_enc_val=20000)
        data_list.append(scan_data)
        strt_idx, end_idx, length, angle, x_dist = map_scan_data.analyze_data(scan_data)
        print(f"length: {length}")
        print(f"angle: {angle}")
        print(f"x_dist: {x_dist}")
        print()
        if angle > 90:
            more += 1
    car.stop_wheels()
    time.sleep(PAUSE)
    print("Wheels Stopped")
    print()
    # Save collected scan data
    # Use remap_scans() to map it.
    with open('corner_data.pkl', 'wb') as f:
        pickle.dump(data_list, f)

def rel_bearing(target):
    """Return 'relative' bearing of an 'absolute' target."""
    delta = target - 180
    rel_brng = car.heading() - delta
    if rel_brng < 0:
        rel_brng += 360
    return rel_brng

def turn_to(target):
    """Turn to target heading (degrees)."""
    # To avoid the complication of the 360 / 0 transition, convert
    # the problem to one of aiming for a target at 180 degrees.
    rel_heading = rel_bearing(target)
    if rel_heading > 180:
        car.spin_ccw(80)
        while rel_heading > 180:
            print(f"relative heading: {rel_heading}")
            rel_heading = rel_bearing(target)
            time.sleep(0.1)
    elif rel_heading < 180:
        car.spin_cw(80)
        while rel_heading < 180:
            print(f"relative heading: {rel_heading}")
            rel_heading = rel_bearing(target)
            time.sleep(0.1)
    car.stop_wheels()

def turn(angle):
    """Spin car angle degrees (CCW positive)."""
    start_heading = car.heading()
    end_heading = start_heading - angle
    if end_heading < 0:
        end_heading += 360
    turn_to(end_heading)


if __name__ == "__main__":

    drive_and_scan()
    car.close()
