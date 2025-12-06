# Importing Libraries: 
import zipfile
# The zipfile module allows you to read and write ZIP archive files. Here it is used to extract a ZIP file containing CSV data.
import os
# The os module provides functions to interact with the operating system, such as creating directories, removing files,
# or listing contents of directories. It’s used here for managing files and directories.
import pandas as pd
# This library is essential for data manipulation and analysis in Python. `pandas` primarily works with DataFrames,
# Here it will be used to load CSV data and then insert that data into a database.
from sqlalchemy import create_engine, inspect, text
# sqlalchemy is a powerful SQL toolkit that allows you to work with relational databases.
#    - `create_engine`: Used to create a connection to a database.
#    - `inspect`: Used to introspect a database (though not used in the given code).
#    - `text`: Allows SQL expressions to be created manually.
from sqlalchemy.orm import sessionmaker
# This function creates a new session for interacting with the database. It is used for database transactions like queries, inserts, or updates. 
from urllib.parse import quote_plus
# Encodes special characters in URLs or connection strings so they are correctly formatted. 
# It’s used to handle special characters (like `@` or `&`) in the database password.
import requests
# A popular library to make HTTP requests. It will be used here to download the ZIP file from a given URL.
from datetime import datetime, timedelta
# These classes are used to work with date and time values in Python. `datetime` allows you to work with specific dates and times, 
# `timedelta` helps in calculating the difference between dates or adding/subtracting time.


# This function is responsible for downloading a ZIP file from a given URL and saving it to the local filesystem. 
# url: The web address from where the ZIP file is to be downloaded.
# zip_file_path: The path where the ZIP file will be saved on the local machine.
def download_zip_file(url, zip_file_path):
# The try block handles any errors that may occur during the downloading process.
    try:
        # os.makedirs Ensures the directory where the ZIP file will be saved. If the directory doesn’t exist, it creates it.
        # os.path.dirname(zip_file_path)`: Extracts the directory path from `zip_file_path`.
        # exist_ok=True`: Ensures no error is raised if the directory already exists
        os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)
        # Defines headers to simulate a browser request. Some websites block requests that don't come from a browser, 
        # so adding a `User-Agent` makes it look like the request is coming from a real browser.
        headers = {'User-Agent': 'Mozilla/5.0'}
        # requests.get: Sends a GET request to download the file from the provided URL.
        # headers: Uses the browser-like header defined earlier.
        # stream=True: Ensures the file is downloaded in chunks rather than all at once, which helps with large files.
        # timeout=10: Limits the time to wait for a response from the server to 10 seconds.
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        # If the response contains an HTTP error (like 404 or 500), this will raise an exception and stop further processing.
        response.raise_for_status()
        # Opens a file at `zip_file_path` in **write-binary mode** (`wb`) to save the downloaded ZIP file.
        with open(zip_file_path, 'wb') as file:
            # Downloads the file in chunks of 1024 bytes (1 KB) and writes these chunks to the file.
            for data in response.iter_content(1024):
                file.write(data)   # Writes the chunk of data to the file.
        print(f"Downloaded file from {url}")
        return True    #indicate that the download was successful.
    # Catches any exceptions related to HTTP requests, such as a failed connection or timeout
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return False


# This function extracts a ZIP file and returns the path of the first csv file it finds.
# zip_file_path: The path to the ZIP file.
# unzip_dir: The directory where the ZIP contents will be extracted.
def unzip_and_find_csv(zip_file_path, unzip_dir):
    try:
        # Checks if the extraction directory already exists.
        if os.path.exists(unzip_dir):
            # Loops through all files in the unzip_dir
            for file in os.listdir(unzip_dir):
                # Joins the directory and file name to get the full file path
                file_path = os.path.join(unzip_dir, file)
                # If the file path points to a regular file:
                if os.path.isfile(file_path):
                    # Deletes the file.
                    os.unlink(file_path)
                # If it’s a directory:
                elif os.path.isdir(file_path):
                    # Removes the directory.
                    os.rmdir(file_path)
        # Opens the ZIP file for reading.
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Extracts all contents of the ZIP file to the `unzip_dir
            zip_ref.extractall(unzip_dir)
        # Loops through the files in the extracted directory. 
        for file in os.listdir(unzip_dir):
            if file.endswith('.csv'):
                print(f"CSV file found: {file}")   #prints file name
                # Returns the full path of the CSV file
                return os.path.join(unzip_dir, file)   
        # If no CSV file is found, raises an error   
        raise FileNotFoundError("No CSV file found in the ZIP archive.")
    # Catches any other exceptions that might occur during extraction
    except Exception as e:
        print(f"Error unzipping file: {e}")
        return None


# This function creates a connection to a MySQL database using SQLAlchemy
# username: The username for the database.
# password: The password for the database.
# host: The hostname (IP address or URL) of the database server.
# port: The port number the database server listens on (e.g., `3306` for MySQL).
# database: The name of the specific database to connect to.
def get_db_engine(username, password, host, port, database):
    # Constructs a connection string in the format required by SQLAlchemy. 
    # It specifies the MySQL driver (`mysql+pymysql://`) and includes the credentials.
    db_connection_string = f'mysql+pymysql://{username}:{quote_plus(password)}@{host}:{port}/{database}'
    print("Creating database engine")
    # Calls `create_engine` to establish a connection to the database and returns the resulting engine.
    return create_engine(db_connection_string)


# This function inserts data from a pandas DataFrame into a SQL table.
# df: The pandas DataFrame containing the data.
# engine: The SQLAlchemy engine created in get_db_engine.
# table_name: The name of the table in the database where data will be inserted.
def insert_data_to_sql(df, engine, table_name):
    try:
        # df.to_sql : This method inserts data from the pandas DataFrame (`df`) into the SQL table.
        # table_name: The name of the target table in the database.
        # con=engine: The SQLAlchemy engine that connects to the database.
        # if_exists='append': If the table already exists, new data is added (appended) to the existing table.
        # index=False: Prevents pandas from inserting the DataFrame index as a column in the table.
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"Data inserted into {table_name}")
    # If any exception occurs during the insertion process, this `except` block catches it.
    except Exception as e:
        # Prints an error message showing what went wrong during the insertion process.    
        print(f"Error inserting data into SQL: {e}")


# This function reads a CSV file into a pandas DataFrame and inserts the data into an SQL table using an SQLAlchemy engine.   
# file_path: The path of the CSV file to be imported.
# db_url: The database connection string (URL).
# table_name: The name of the table in which data from the CSV file will be inserted.
def import_csv_to_db(file_path, db_url, table_name):
    try:
        # Reads the CSV file into a pandas DataFrame.
        df = pd.read_csv(file_path)
        # Creates an SQLAlchemy engine using the database connection URL (`db_url`). This engine will be used to insert data into the database.
        engine = create_engine(db_url)
        # df.to_sql: Inserts the DataFrame data into the specified SQL table (`table_name`).
        # con=engine: The SQLAlchemy engine used to connect to the database.
        # if_exists='append'`: If the table already exists, the data is appended.
        # index=False: Prevents pandas from inserting the DataFrame index as a column.
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        # Prints a confirmation message indicating that the data from the CSV file has been successfully imported into the specified SQL table.
        print(f"Data from {file_path} imported into {table_name}")
    except Exception as e:
        print(f"Error importing CSV to DB: {e}")
# This function checks whether a given date is a business day (not a weekend or holiday) using a database.
# date_input: The date to check, provided as a string in the format `YYYYMMDD`.
# engine: The SQLAlchemy engine that connects to the database
def is_business_day(date_input, engine):
    try:
        # datetime.strptime: Converts the `date_input` string into a `datetime` object. This allows us to manipulate the date more easily
        # (e.g., checking if it’s a weekend).
        # The date format is expected to be `'%Y%m%d'` (e.g., `20231011` for October 11, 2023).
        date_obj = datetime.strptime(date_input, '%Y%m%d')
        # date_obj.weekday()`**: Returns the day of the week as an integer (0 = Monday, 6 = Sunday). 
        # If `weekday() >= 5`, it means the date falls on a Saturday (5) or Sunday (6)
        if date_obj.weekday() >= 5:
            return False
        # Open a connection to the database using the SQLAlchemy engine.
        with engine.connect() as connection:
            # text() Constructs a raw SQL query to check the number of rows in `holidays` table where `date` column matches the `date_input`. 
            # This query will return a count of holidays on the given date.
            query = text(f"SELECT COUNT(*) FROM holidays WHERE date = '{date_input}'")
            # connection.execute(query): Executes the SQL query and retrieves the result.
            # .scalar(): Gets the first value of the query result, which is the count of matching holidays. 
            # If the count is 0, the date is not a holiday, so the function returns `True`, meaning it’s a business day.
            # If the count is greater than 0, the function returns `False`, meaning it’s a holiday (not a business day)
            return connection.execute(query).scalar() == 0
    except Exception as e:
        print(f"Error checking business day: {e}")
        return False


# This function automates the process of downloading a ZIP file for a specific date, extracting a CSV from it, 
# cleaning the data by renaming columns, and then inserting the data into a database table.
# Defines the function `process_date` with six parameters:
# date_input: A string representing the date (e.g., `'20231011'`).
# engine: The SQLAlchemy engine used to connect to the database.
# table_name: The name of the database table where data will be inserted.
# unzip_dir: The directory where the ZIP file will be extracted.
# url_template: A template string that contains the URL format for downloading the ZIP file. It has placeholders to insert `date_input`.
# column_mapping: A dictionary that maps old column names in the CSV to new names for the DataFrame.
def process_date(date_input, engine, table_name, unzip_dir, url_template, column_mapping):
    # url_template.format: Replaces the placeholder `{date_input}` in `url_template` with the actual `date_input` value, generating the full download URL for the ZIP file.
    url = url_template.format(date_input=date_input)
    # Defines the local path where the ZIP file will be saved. The path uses the `date_input` to make each ZIP file's name unique (e.g., `BhavCopy_20231011.zip`).
    zip_file_path = f"C:\\Users\\Khomane.Digambar\\Downloads\\BhavCopy_{date_input}.zip"
    # download_zip_file`**: Calls the function that downloads the ZIP file from the URL and saves it to `zip_file_path`.
    # If the download fails (returns `False`), the function stops with `return`.
    if not download_zip_file(url, zip_file_path):
        return
    # `unzip_and_find_csv`: Calls a function that extracts ZIP file contents and searches for a CSV file inside the extracted files. The path to CSV file is returned.
    csv_file_path = unzip_and_find_csv(zip_file_path, unzip_dir)
    # If no CSV file is found (i.e., `csv_file_path` is `None`), the function stops with `return`.
    if csv_file_path is None:
        return
    # pd.read_csv`**: Reads the CSV file into a pandas DataFrame (`df`).
    # If an error occurs (e.g., the file is corrupt or not found), it is caught in the `except` block, and the error message is printed.
    # If reading the CSV fails, the function exits with `return`.
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading CSV file for {date_input}: {e}")
        return
    # df.rename: Renames the DataFrame columns according to the `column_mapping` dictionary.
    # inplace=True: Ensures the renaming happens directly on the DataFrame, without needing to reassign it.
    df.rename(columns=column_mapping, inplace=True)
    # inspect(engine).get_columns(table_name)`**: Uses SQLAlchemy’s `inspect` function to get the column names from the specified `table_name` in the database. This ensures that the DataFrame matches the structure of the SQL table.
    # The `get_columns` method returns a list of dictionaries, each containing information about a column, including its name.
    # `col['name']`: Extracts the column name from each dictionary.
    try:
        sql_columns = [col['name'] for col in inspect(engine).get_columns(table_name)]
        # Subsets the DataFrame to only include the columns that match the columns in the SQL table. This ensures the DataFrame is aligned with the table's structure.
        df = df[sql_columns]
    # If an error occurs (e.g., a column in the DataFrame doesn’t match the SQL table), it is caught in the `except` block, and an error message is printed. 
    except Exception as e:
        print(f"Error matching DataFrame columns with SQL for {date_input}: {e}")
        return
    # insert_data_to_sql: Calls a previously defined function to insert the cleaned and aligned DataFrame (`df`) into the SQL table.
    # The function uses the SQLAlchemy engine to perform the insertion.
    insert_data_to_sql(df, engine, table_name)
# This function updates the `summary` table with cumulative counts of `cm` and `fo` records between the given `start_date` and `end_date`. 
# It uses a database connection via `engine`
def update_summary_table(start_date, end_date, engine):
    # datetime.strptime`**: Converts the `start_date` and `end_date` strings from the format `YYYYMMDD` (e.g., `'20231011'`) into `datetime` objects for easier manipulation.
    start_date = datetime.strptime(start_date, '%Y%m%d')
    end_date = datetime.strptime(end_date, '%Y%m%d')
    # Initializes two counters to track the cumulative counts for `cm` and `fo`. These will be used to aggregate the data over the date range.
    cumulative_cm_count = 0
    cumulative_fo_count = 0
    # `sessionmaker(bind=engine)`**: Creates a new session factory that is bound to the provided `engine` (SQLAlchemy engine).
    # `session = Session()`**: Instantiates a session for interacting with the database. This session will be used to execute SQL queries and manage transactions.
    Session = sessionmaker(bind=engine)
    session = Session()
    # current_date = start_date : Initializes the loop with the `start_date`.
    current_date = start_date
    # while current_date <= end_date : Loops through each day from `start_date` to `end_date` inclusive
    while current_date <= end_date:
        date_str = current_date.strftime('%Y%m%d')
        if is_business_day(date_str, engine):
            # cm_query : Defines an SQL query that selects the count of rows in the `raw_cm_bhawcopy` table for the current `trade_date`.
            # pd.read_sql : Executes the SQL query and returns the result as a pandas DataFrame.
            # .iloc[0, 0] : Retrieves the count (first row, first column) from the DataFrame result.
            # The `cm_count` variable holds the count of `cm` records for the current date.
            cm_query = f"SELECT COUNT(*) FROM raw_cm_bhawcopy WHERE trade_date = '{date_str}'"
            cm_count = pd.read_sql(cm_query, engine).iloc[0, 0]
            # Similar to the `cm_query`, this query counts the rows in the `raw_fo_bhawcopy` table for the current `trade_date`.
            # The `fo_count` variable holds the count of `fo` records for the current date.
            fo_query = f"SELECT COUNT(*) FROM raw_fo_bhawcopy WHERE trade_date = '{date_str}'"
            fo_count = pd.read_sql(fo_query, engine).iloc[0, 0]
            # Updates the cumulative counts for both `cm` and `fo` by adding the counts from the current date.
            cumulative_cm_count += cm_count
            cumulative_fo_count += fo_count
            # summary_query : Constructs an SQL query that inserts the cumulative counts into the `summary` table for the `trade_date`.
            # If the `trade_date` already exists in the table, the `ON DUPLICATE KEY UPDATE` clause updates the existing row with the new cumulative counts.
            # The `current_date.strftime('%Y-%m-%d')` ensures the date is in the format `YYYY-MM-DD` for SQL insertion.
            # session.execute(summary_query) : Executes the SQL query using the current session.
            summary_query = text(f"""
            INSERT INTO summary (trade_date, count_cm, count_fo)
            VALUES ('{current_date.strftime('%Y-%m-%d')}', {cumulative_cm_count}, {cumulative_fo_count})
            ON DUPLICATE KEY UPDATE
            count_cm = {cumulative_cm_count},
            count_fo = {cumulative_fo_count}
            """)
            session.execute(summary_query)
        #Skipping Non-Business Days 
        else:
            print(f"{date_str} is not a business day. Skipping.")
        # Moving to the Next Date
        # timedelta(days=1) : Advances the `current_date` by one day, so the loop can move to the next date.
        current_date += timedelta(days=1)
    # Committing the Transaction
    # session.commit(): Commits the transaction to the database, ensuring all the inserted or updated rows are saved.
    session.commit()
    # Closing the Database Session
    # `session.close()`**: Closes the database session to release the connection resources.
    session.close()


#   the `main` function, the starting point of your script.
def main():
    start_date_input = input("Enter the start date in YYYYMMDD format: ")
    end_date_input = input("Enter the end date in YYYYMMDD format: ")
    # Directory for Unzipped Files
    # unzip_dir: Specifies the directory where ZIP files will be extracted. The `r` before the string ensures that backslashes are treated as literal characters.
    unzip_dir = r"C:\\Users\\Khomane.Digambar\\Downloads\\unzip"
    # Database Credentials and Connection
    # Sets up the database connection details (username, password, host, port, and database name).
    username = 'root'
    password = 'cfg@1234'
    host = 'localhost'
    port = 3306
    database = 'py_auto'
    # get_db_engine(): This function is called to create a SQLAlchemy engine using the provided credentials, which will be used for connecting to the database.
    engine = get_db_engine(username, password, host, port, database)

    # Importing a CSV File into the Database
    # **`new_file_path`**: Specifies the path of the CSV file (`example.csv`) that will be imported into the `holidays` table in the database.
    new_file_path = r'C:\\Users\\Khomane.Digambar\\Downloads\\example.csv'
    new_table_name = 'holidays'
    # - **`db_url`**: Constructs the full database URL for the connection.
    db_url = f'mysql+pymysql://{username}:{quote_plus(password)}@{host}:{port}/{database}'
    # - **`import_csv_to_db()`**: Calls this function to import the CSV file located at `new_file_path` into the `holidays` table.  
    import_csv_to_db(new_file_path, db_url, new_table_name)
    # Converting the Date Input to DateTime Objects
    start_date = datetime.strptime(start_date_input, '%Y%m%d')
    end_date = datetime.strptime(end_date_input, '%Y%m%d')
    # URL Templates for Data Download
    # url_templates: A dictionary that holds URL templates for downloading ZIP files containing `raw_cm_bhawcopy` and `raw_fo_bhawcopy` data. 
    # The `{date_input}` placeholder will be replaced with the actual date in later code.
    url_templates = {
        'raw_cm_bhawcopy': "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_input}_F_0000.csv.zip",
        'raw_fo_bhawcopy': "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date_input}_F_0000.csv.zip"
    }
    # column_mappings: A dictionary that provides mappings from the original column names in the CSV files to the desired column names in the DataFrame.
    # These mappings will be used to rename the DataFrame columns during processing.
    column_mappings = {
        'raw_cm_bhawcopy': {
            'TradDt': 'trade_date',
            'ISIN': 'isin',
            'TckrSymb': 'symbol',
            'SctySrs': 'series',
            'OpnPric': 'open_price',
            'HghPric': 'high_price',
            'LwPric': 'low_price',
            'ClsPric': 'close_price',
            'LastPric': 'last_traded_price',
            'PrvsClsgPric': 'previous_close',
            'TtlTradgVol': 'total_traded_qty',
            'TtlTrfVal': 'total_traded_value',
            'TtlNbOfTxsExctd': 'number_of_trades'
        },
        'raw_fo_bhawcopy': {
            'FinInstrmTp': 'instrument',
            'TckrSymb': 'symbol',
            'XpryDt': 'expiry_date',
            'StrkPric': 'strike_price',
            'OptnTp': 'option_type',
            'OpnPric': 'open_price',
            'HghPric': 'high_price',
            'LwPric': 'low_price',
            'ClsPric': 'close_price',
            'SttlmPric': 'settle_price',
            'TtlTradgVol': 'total_traded_contract',
            'TtlTrfVal': 'total_traded_value',
            'OpnIntrst': 'oi',
            'ChngInOpnIntrst': 'delta_oi',
            'TradDt': 'trade_date'
        }
    }
    # Looping Through the Date Range
    current_date = start_date                       # Initializes `current_date` with the `start_date`
    while current_date <= end_date:                 # Loops through each day between the `start_date` and `end_date`.
        date_str = current_date.strftime('%Y%m%d')  # Formats the `current_date` as a string in `YYYYMMDD` format for use in the URLs and SQL queries.
        # Processing Each Business Day
        # Calls the `is_business_day` function to check if the `date_str` corresponds to a business day
        if is_business_day(date_str, engine):
            # Loops through the `url_templates` dictionary to process both the `raw_cm_bhawcopy` and `raw_fo_bhawcopy` data.
            for table_name, url_template in url_templates.items():
                # Calls the `process_date` function to download the ZIP file, extract the CSV, rename the columns, and insert the data into the database.
                process_date(date_str, engine, table_name, unzip_dir, url_template, column_mappings[table_name])
        # Skipping Non-Business Days 
        else:
            print(f"{date_str} is not a business day. Skipping.")
        # Moving to the Next Date
        # Advances the `current_date` by one day and repeats the loop until the `end_date` is reached
        current_date += timedelta(days=1)
    #  Updating the Summary Table
    # After processing all the dates, this function is called to update the `summary` table with cumulative data from the date range.
    update_summary_table(start_date_input, end_date_input, engine)
# if __name__ == "__main__" : This ensures that the `main` function is only executed when the script is run directly, not when it is imported as a module in another script.
# main(): Calls the `main` function to start the process.
if __name__ == "__main__":
    main()
   