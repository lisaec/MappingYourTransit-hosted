
#SQL statements to make each table
build_tables = [ 
    """CREATE TABLE IF NOT EXISTS agency (
            agency_id TEXT PRIMARY KEY,
            agency_name TEXT, 
            agency_url  TEXT, 
            agency_timezone TEXT, 
            agency_lang TEXT,
            agency_phone TEXT,
            agency_fare_url TEXT,
            agency_email TEXT
        );""",

    """CREATE TABLE IF NOT EXISTS stops (
            stop_id TEXT PRIMARY KEY, 
            parent_station TEXT,
            stop_code TEXT, 
            stop_name TEXT, 
            tts_stop_name TEXT, 
            stop_desc TEXT, 
            stop_lat FLOAT, 
            stop_lon FLOAT, 
            zone_id TEXT,
            stop_url TEXT,
            location_type INTEGER,
            vehicle_type INTEGER,
            wheelchair_boarding INTEGER,
            level_id TEXT,
            platform_code TEXT,
            FOREIGN KEY (parent_station) REFERENCES stops (stop_id)
        );""",

        """CREATE TABLE IF NOT EXISTS routes (
            route_id TEXT PRIMARY KEY, 
            agency_id TEXT, 
            parent_station TEXT,
            route_desc TEXT, 
            route_short_name TEXT,
            route_long_name TEXT,
            route_type INTEGER, 
            route_url TEXT, 
            route_color TEXT, 
            route_text_color TEXT, 
            route_sort_order INTEGER,
            continuous_pickup TEXT,
            location_type INTEGER,
            FOREIGN KEY (agency_id) REFERENCES agency (agency_id), 
            FOREIGN KEY (parent_station) REFERENCES stops (stop_id)
        
        );""",

        """
            CREATE TABLE IF NOT EXISTS calendar (
            service_id TEXT PRIMARY KEY,
            monday INTEGER NOT NULL,
            tuesday INTEGER NOT NULL,
            wednesday INTEGER NOT NULL,
            thursday INTEGER NOT NULL,
            friday INTEGER NOT NULL,
            saturday INTEGER NOT NULL,
            sunday INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        );""",


        """CREATE TABLE IF NOT EXISTS trips (
            trip_id TEXT PRIMARY KEY, 
            route_id TEXT,
            service_id TEXT, 
            trip_headsign TEXT, 
            trip_short_name TEXT, 
            direction_id TEXT, 
            block_id TEXT, 
            shape_id TEXT,
            wheelchair_accessible INTEGER,
            bikes_allowed INTEGER,
            FOREIGN KEY (route_id) REFERENCES routes (route_id), 
            FOREIGN KEY (service_id) REFERENCES calendar (service_id),
            FOREIGN KEY (shape_id) REFERENCES shapes(shape_id)
        );""" ,
    
    
        """CREATE TABLE IF NOT EXISTS stop_times (
                trip_id TEXT,
                arrival_time TEXT,
                departure_time TEXT,
                stop_id TEXT,
                location_id TEXT,
                stop_sequence INTEGER,
                stop_headsign TEXT,
                start_pickup_drop_off_window TEXT,
                end_pickup_drop_off_window TEXT,
                pickup_type INTEGER,
                drop_off_type INTEGER,
                continuous_pickup INTEGER,
                continuous_drop_off INTEGER,
                shape_dist_traveled FLOAT,
                timepoint INTEGER,
                pickup_booking_rule_id TEXT,
                drop_off_booking_rule_id TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips (trip_id),
                FOREIGN KEY (stop_id) REFERENCES stops (stop_id)

        );""",
    
        """CREATE TABLE IF NOT EXISTS calendar_dates (
                service_id TEXT PRIMARY KEY, 
                date DATE,
                exception_type INTEGER, 
                FOREIGN KEY (service_id) REFERENCES calendar (service_id)

        );""" ,
    
        """ CREATE TABLE IF NOT EXISTS shapes (
            
                shape_id TEXT,
                shape_pt_lat FLOAT,
                shape_pt_lon FLOAT,
                shape_pt_sequence INT,
                shape_dist_traveled FLOAT
                
                );""",
    
        """CREATE TABLE IF NOT EXISTS transfers (
            from_stop_id TEXT,
            to_stop_id TEXT,
            from_route_id TEXT,
            to_route_id TEXT,
            from_trip_id TEXT,
            to_trip_id TEXT,
            transfer_type INTEGER,
            min_transfer_time INTEGER,

            FOREIGN KEY (from_stop_id) REFERENCES stops(stop_id),
            FOREIGN KEY (to_stop_id) REFERENCES stops(stop_id),
            FOREIGN KEY (from_route_id) REFERENCES routes(route_id),
            FOREIGN KEY (to_route_id) REFERENCES routes(route_id),
            FOREIGN KEY (from_trip_id) REFERENCES trips(trip_id),
            FOREIGN KEY (to_trip_id) REFERENCES trips(trip_id)

        );"""

]

#SQL statement to get hourly frequency by route
route_freq_sql = """SELECT 
        trips.route_id,
        CAST(SUBSTR(arrival_time, 1, 2) AS INTEGER) AS hour,
        COUNT(*) AS trip_count
    FROM stop_times
    JOIN trips ON stop_times.trip_id = trips.trip_id
    WHERE arrival_time IS NOT NULL
      AND CAST(SUBSTR(arrival_time, 1, 2) AS INTEGER) BETWEEN 8 AND 20
      AND trips.route_id IN (
          SELECT route_id
          FROM stop_times
          JOIN trips ON stop_times.trip_id = trips.trip_id
          WHERE arrival_time IS NOT NULL
            AND CAST(SUBSTR(arrival_time, 1, 2) AS INTEGER) BETWEEN 8 AND 20
          GROUP BY route_id
          ORDER BY COUNT(*) DESC
          LIMIT 10
      )
    GROUP BY trips.route_id, hour
    ORDER BY trips.route_id, hour;"""