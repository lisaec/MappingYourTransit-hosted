import pandas as pd
import matplotlib.pyplot as plt
import os
from typing import Type
from src import my_sql
import sqlite3
from shapely.geometry import LineString


#creating a class for reading in the feed data

class Feed:
    """This class holds the data for each GTFS feed uploaded/selected. It creates a database for the feed and includes methods for accessing each table, pre-processing geospatial data, and creating map features"""
    def __init__(
    self,
    gtfs_path: str
    ):
        #defining file paths
        self._gtfs_path = gtfs_path
        self.name = os.path.basename(os.path.normpath(gtfs_path))
        self.parent_dir = os.path.dirname(os.path.dirname(gtfs_path))
        self.db_path = os.path.join(self.parent_dir, "databases", f"{self.name}.db")

         # Check for required files
        self._validate_required_files()

        #connecting to database
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        #creating database if it doesn't exist
        if not self._database_exists():
            self._create_tables()
            self._insert_data()

    #file overviews
    def gtfs_path(self):
        """path to data"""
        return self._gtfs_path
    
    def get_files(self):
        """list of files in gtfs"""
        return os.listdir(self._gtfs_path)
    
    def _validate_required_files(self):

        """Checks if all required files are present in gtfs folder and raises an error if not"""
        REQUIRED_FILES = [
        "agency.txt",
        "stops.txt",
        "routes.txt",
        "shapes.txt",
        "trips.txt",
        "stop_times.txt"
        ]
        missing_files = []
        for filename in REQUIRED_FILES:
            if filename not in self.get_files():
                missing_files.append(filename)
        if missing_files:
            raise FileNotFoundError(
                f"Missing required GTFS files in {self._gtfs_path}: {', '.join(missing_files)}"
            )
        return None
    
    #methods to access each file
    
    #essential files present in MOST GTFS 
    def stops(self):
        return extract_file('stops.txt', self)
    
    def routes(self):
        return extract_file('routes.txt', self)
    
    def trips(self):
        return extract_file('trips.txt', self)
    
    def agency(self):
        return extract_file('agency.txt', self)

    def calendar_dates(self):
        return extract_file('calendar_dates.txt', self)

    def stop_times(self):
        return extract_file('stop_times.txt', self)

    #cond. required
    def calendar(self):
        return extract_file('calendar.txt', self)
    
   #cond. required
    def shapes(self):
        return extract_file('shapes.txt', self)
    
    #not required
    def transfers(self):
        return extract_file('transfers.txt', self)
    
    #Building the database
    def _database_exists(self) -> bool:
        """Checks if the example essential table 'agency' exists  """
        self.cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='agency';
        """)
        return bool(self.cursor.fetchone())


    def _create_tables(self):
        """builds tables using sql in my_sql.py"""
        table_statements = my_sql.build_tables
        for statement in table_statements:
            self.cursor.execute(statement)
        self.conn.commit()
        return None
    
    def _get_table_columns(self, table_name: str)-> list:
        """Gets the columns of a table so that the dfs uploaded can be filtered (avoids errors)"""
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in self.cursor.fetchall()]  


    def insert_dataframe(self, df: pd.DataFrame, table_name: str):
        """inserts data from a pandas dataframe for each table to the database"""
        #removes columns that don't go in the final database (optional columns, non-standard columns)
        filtered_df = df[[col for col in df.columns if col in self._get_table_columns(table_name)]]
        columns = filtered_df.columns.tolist()
        placeholders = ', '.join(['?'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        #insert data
        for _, row in filtered_df.iterrows():
            values = [None if pd.isna(val) else val for val in row]
            self.cursor.execute(insert_sql, values)

        self.conn.commit()
        return None

    def _insert_data(self):
        """inserts data into database for all ESSENTIAL files"""
        self.insert_dataframe(self.agency(), 'agency')
        self.insert_dataframe(self.stops(), 'stops')
        self.insert_dataframe(self.shapes(), 'shapes')
        self.insert_dataframe(self.routes(), 'routes')
        self.insert_dataframe(self.trips(), 'trips')
        self.insert_dataframe(self.stop_times(), 'stop_times')

        return None

    def close(self):
        self.conn.close()
    
    #spatial features
    def center_pt(self) -> tuple[int, int]:
        """Returns a lat/lon tuple of the center of the transit network"""
        center = [self.shapes()['shape_pt_lat'].mean(), self.shapes()['shape_pt_lon'].mean()]
        return center
    
    def shape_pts(self)-> pd.Series:
        """returns series with the points on each route as a list of Linestring coordinate tuples
        currently slow and doesn't access database"""
        
        shape_points = self.shapes().groupby("shape_id")[["shape_pt_lat", "shape_pt_lon"]].apply(
            lambda g: LineString(g.values))
        
        #naming series for later joins
        shape_points.name = 'shape_points'
    
        return shape_points
    

    
    def trips_shapes_routes(self) -> pd.DataFrame:
        """returns Dataframe with trip, route, and shape data for mapping. removes 
        duplicate linesrtrings"""

        sql = """
                SELECT 
                    trips.*, 
                    routes.route_id,
                    routes.route_long_name,
                    routes.route_short_name,
                    CASE 
                        WHEN LOWER(routes.route_color) = 'ffffff' THEN '000000'
                        ELSE routes.route_color
                    END AS route_color
                FROM trips
                JOIN routes USING (route_id)
                WHERE shape_id IS NOT NULL
                AND routes.route_color IS NOT NULL;
                """
                
        trips_routes = pd.read_sql(sql, self.conn)
        shapes = self.shape_pts().to_frame().reset_index()

        trips_routes['shape_id'] = trips_routes['shape_id'].astype(str)
        shapes['shape_id'] = shapes['shape_id'].astype(str)
        
        trips_shapes_routes = trips_routes.merge(shapes, on='shape_id', how='left')


        #removing duplicate linestrings for speed and clean-ness
        def normalize_linestring(ls):
            """organizes linestrings smallest to largest"""
            coords = list(ls.coords)
            return tuple(coords if coords[0] <= coords[-1] else coords[::-1])

        trips_shapes_routes['normalized'] = trips_shapes_routes['shape_points'].apply(normalize_linestring)
        trips_shapes_routes_unique = trips_shapes_routes.drop_duplicates(subset='normalized').copy()
        trips_shapes_routes_unique.drop(columns='normalized', inplace=True)

        
        return trips_shapes_routes_unique
    
    #other functions
    def agency_name(self) -> str:
        "Returns agency name as a string"
        return self.agency()['agency_name'][0]
    
    #other functions
    def agency_url(self) -> str:
        "Returns agency url as a string"
        return self.agency()['agency_url'][0]
        

    def departure_info(self)-> dict:
        """"returns a dictionary of departure info by stop id for pop ups"""

        times = self.stop_times()

        #converting departure time to a time format to get frequency
        times['departure_time'] = pd.to_timedelta(times['departure_time'])

        #info for each stop
        grouped = times.groupby(['stop_id'])
        
        dept_info = {}

        for stop_id, group in grouped:
            times = group['departure_time'].sort_values()
            #if there is only one departure, there is no frequency to measure
            if len(times) < 2:
                freq = "Infrequent"
            else:
                deltas = times.diff().dropna()
                avg_freq = deltas.mean()
                freq = f"Every {int(avg_freq.total_seconds() // 60)} minutes"

            first = str(times.min()).split(" ")[-1][:-3]
            last = str(times.max()).split(" ")[-1][:-3]
            count = len(times)

            dept_info[stop_id[0]] = f"{count} daily departures: {freq} from {first} to {last}"
            
        return dept_info
    

    def route_freq(self):
        """returns table of top 10 routes and hourly frequency"""
        route_freq = pd.read_sql(my_sql.route_freq_sql, self.conn)
        pivot = route_freq.pivot(index='route_id',  columns='hour', values='trip_count').fillna(0)
        return pivot
    
    
def extract_file(file: str, feed: Type['Feed'])-> pd.DataFrame:
    """reads csv for individual table methods"""

    files = feed.get_files()
    gtfs_path = feed.gtfs_path()
    
    file_path = f"{gtfs_path}/{file}"

    if file in files:
        data = pd.read_csv(file_path)
        return data
    
    else:
        return None
    



