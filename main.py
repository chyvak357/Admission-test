# UTF-8, Python 3.6.2
from ftplib import FTP
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import json
import os
import logging
from sys import stdout
from time import sleep
import random
from copy import deepcopy

MAX_CONNECTIONS = 10
MAX_PROCESSING_THREADS = 2

"""
Example configuration file contents

    [{
        "server": {
            "host": "192.168.0.104",
            "port": "2121",
            "login": "admin",
            "password": "1234"
        },
        "file": {
            "local_path": "D:/Exemple/of/path/file.dwg",
            "server_path": "LocalPath/subfolder1"
        }
    }]
    
"""


class JsonChecker():
    """  Main thread to wait and start processing JSON configuration files  """

    def __init__(self):

        self.pool_file_transfer = ThreadPoolExecutor(MAX_PROCESSING_THREADS)
        self.pool_connections = ThreadPoolExecutor(MAX_CONNECTIONS)
        self.run()


    def run(self):
        while True:
            """  'files' - The folder to which the configuration files will go after processing  """

            json_files_list = os.listdir('files')

            for json_file in json_files_list:
                try:
                    os.rename('files/' + json_file, 'checked/' + json_file)

                except PermissionError as err:
                    log.error('JsonChecker: Config file err, {}'.format(err))
                    continue

                except FileExistsError:
                    os.rename('files/' + json_file, 'checked/' + '(1)' + json_file)

                else:
                    log.info(json_file + " checked")
                    self.pool_file_transfer.submit(FileTransfer, json_file, self.pool_connections)
            sleep(5)



class FileTransfer():
    """  Thread for processing config files and transfer data from them  """

    def __init__(self, file_name, pool_connections):

        # the variable stores the relative path to the configuration file
        self.file_path = 'checked/' + file_name
        self.pool_connections = pool_connections
        self.run()


    def run(self):
        json_data = self.config_file_processing()

        for obj in json_data:
            self.pool_connections.submit(FileTransfer.th_connect_transfer, self, obj)


    def th_connect_transfer(self, obj):
        """  Function to connect to the server and transfer files. Works in thread   """

        for errs in range(3):
            connection = self.ftp_connect(obj)

            if connection != 1:
                break
            elif errs == 2:
                log.error('FileTransfer was stopped, connection err for {}'.format(obj['file']['local_path']))
                return 1

            sleep(2)

        self.file_transfer(connection, obj['file']['local_path'], obj['file']['server_path'])
        try:
            connection.close()
        except ConnectionAbortedError:
            pass


    def config_file_processing(self):
        """  Reading and return json data from config file"""

        with open(self.file_path, "r") as read_file:
            json_data = json.load(read_file)
        return json_data


    def ftp_connect(self, data):
        """  Connection to FTP server function """

        message = 'host: {}; port: {}, login: {};'.format(data['server']['host'], data['server']['port'], data['server']['login'])

        ftp_connection = FTP()
        try:
            ftp_connection.connect(data['server']['host'], int(data['server']['port']))
        except (ConnectionRefusedError, TimeoutError, ConnectionResetError) as err:
            log.error('Connection err: {} for {};'.format(err, message))
            return 1

        else:
            try:
                ftp_connection.login(data['server']['login'], data['server']['password'], 'TransferScript')

            except (ConnectionRefusedError, TimeoutError, ConnectionResetError) as err:
                log.error('{} for {};'.format(err, message))
                return 1

            else:
                log.info('Conn returned for ' + message)

                ftp_connection.encoding = 'utf-8'
                return ftp_connection



    def file_transfer(self, connection, local_path, server_path):
        """
        Function for transfer files on server

        'connection' contain ftp connection to server
        'local_path' path to file on local disk
        'server_path' is the direct path to the file on the server

        """

        try:
            with open(local_path, "rb") as file:
                try:
                    if FileTransfer.check_ftp_folder(self, connection, server_path) == 0:
                        # the working folder is no longer at the root of the server for current connection
                        connection.storbinary('STOR ' + os.path.split(local_path)[-1], file)

                except (ConnectionResetError, TimeoutError, ConnectionAbortedError) as err:
                    log.error('Transfer Error. File: {}. {}'.format(local_path, err))
                    return 1

        except FileNotFoundError as err:
            log.error('Transfer Error. File: {}. {}'.format(local_path, err))

        else:
            log.info('Successfully transferred: {}'.format(local_path))


    def check_ftp_folder(self, connection, path_str):
        """
        The function checks for availability and creates folders for storing the file on the server

        'path_str' contain direct path to the file on the server
        """

        path = path_str.split('/')
        for folder in path:
            if folder not in connection.nlst():
                for i in range(3):
                    try:
                        connection.mkd(folder)
                        connection.cwd(folder)
                    except Exception as err:
                        if i == 2:
                            log.error('Folder {} cannot be create: {}'.format(folder, err))
                            return 1
                    else:
                        break

            else:
                connection.cwd(folder)

        return 0


class TestGenerator(Thread):
    """
    An automatic test of 10 files to demonstrate and debug functions

    Folder 'test files' contain set of several files including cyrillic in the title
    The function creates a configuration file in the working folder
    and then moves it to the "files" folder where it will be processed by the main part of program

    """

    def __init__(self, name):
        Thread.__init__(self)
        self.name = name

        self.path = 'test files'
        self.file_list = os.listdir(self.path)
        self.server_folders_list = ['Folder1', 'Folder1/subfolder1', 'Folder1/subfolder1/subfolder12', 'Folder2',
                                    'Folder3']

        self.json_template = {
            "server": {
                "host": "192.168.1.95",
                "port": "2125",
                "login": "admin",
                "password": "1234"
            },
            "file": {
                "local_path": "",
                "server_path": ""
            }
        }

    def run(self):

        for i in range(10):
            sleep(random.randint(1,6))

            tmp_json_data = []
            for j in range(random.randint(1,4)):
                tmp_json_data.append(deepcopy(self.json_template))
                tmp_json_data[-1]['file']['local_path'] = os.path.abspath(self.path + '/' + random.choice(self.file_list))
                tmp_json_data[-1]['file']['server_path'] = random.choice(self.server_folders_list)


            temp_name = 'data_json_' + str(i) + '_' + str(int(random.random()*1000)) + '.json'
            with open(temp_name, "w") as write_file:
                json.dump(tmp_json_data, write_file, ensure_ascii=False,)

            os.rename(temp_name, 'files/' + temp_name)


def logger_creator():
    """ Creating a logger for recording """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler('logs.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger



if __name__ == "__main__":
    log = logger_creator()

    # Uncommit this lines to run the test
    test_thread = TestGenerator('test')
    test_thread.start()

    main_thread = JsonChecker()
