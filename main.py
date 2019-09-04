# UTF-8, Python 3.6.2
from ftplib import FTP
from threading import Thread
import json
import os
import logging
import time
import random


"""

Example configuration file contents

json_string = 
    {
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
    }
    
"""


class JsonChecker(Thread):
    """  Main thread to wait and start processing JSON configuration files  """

    def __init__(self, name):
        Thread.__init__(self)
        self.name = name
        print("!-- JsonChecker launched")


    def run(self):
        while True:
            """ 'files' - The folder to which the configuration files will go after processing"""

            json_files_list = os.listdir('files')

            for json_file in json_files_list:
                try:
                    os.rename('files/' + json_file, 'checked/' + json_file)

                except (PermissionError, FileExistsError) as err:
                    log.error('JsonChecker: Config file err', err)
                    print('!-- PermissionError', err)
                    continue

                except FileExistsError:
                    os.rename('files/' + json_file, 'checked/' + '(1)' + json_file)

                else:
                    file_transfer_thread = FileTransfer('checked/' + json_file, json_file)
                    file_transfer_thread.start()
                    log.info(json_file + " - checked")


class FileTransfer(Thread):
    """  Thread for processing config files and transfer data from them  """

    def __init__(self, file_path, name='deffault'):
        Thread.__init__(self)
        self.name = name

        # the variable stores the relative path to the configuration file
        self.file_path = file_path

    def run(self):
        json_data = self.config_file_processing()

        # Several connection attempts in 5 second intervals
        for errs in range(3):
            connection = self.ftp_connect(json_data)

            if connection != 1:
                break
            elif errs == 2:
                log.error('FileTransfer was stopped, connection err')
                print("!--- ERR FileTransfer was stopped")
                return 1
            time.sleep(5)

        self.file_transfer(connection, json_data['file']['local_path'], json_data['file']['server_path'])
        try:
            connection.close()
        except ConnectionAbortedError:
            pass


    def config_file_processing(self):
        """  Reading and return json data from config file"""

        with open(self.file_path, "r") as read_file:
            json_data = json.load(read_file)
            read_file.close()
        return json_data


    def ftp_connect(self, data):
        """  Connection to FTP server function """

        print("!- Connection is called")
        log.info("FTP connection is called")
        message = 'host: {}; port: {}, login: {};'.format(data['server']['host'], data['server']['port'], data['server']['login'])

        ftp_connection = FTP()
        try:
            ftp_connection.connect(data['server']['host'], int(data['server']['port']))
        except (ConnectionRefusedError, TimeoutError, ConnectionResetError) as err:
            print('!--- Err connection 1. {}. {};'.format(err, message))
            log.error('{}. {};'.format(err, message))
            return 1

        else:
            try:
                ftp_connection.login(data['server']['login'], data['server']['password'], 'TransferScript')
            except (ConnectionRefusedError, TimeoutError, ConnectionResetError) as err:
                print('!--- Err login. {}. {};'.format(err, message))
                log.error('{}. {};'.format(err, message))
                return 1

            else:
                print('!- FTP connection successfully returned ' + message)
                log.info('FTP connection successfully returned ' + message)

                ftp_connection.encoding = 'utf-8'
                return ftp_connection



    def file_transfer(self, connection, local_path, server_path):
        """
            Function for transfer files on server

            'connection' contain ftp connection to server
            'local_path' path to file on local disk
            'server_path' is the direct path to the file on the server

        """

        print('!- Transfer ' + local_path)
        log.info('Transfer started' + local_path)
        try:
            with open(local_path, "rb") as file:
                try:
                    if self.check_ftp_folder(connection, server_path) == 0:
                        # the working folder is no longer at the root of the server
                        connection.storbinary('STOR ' + os.path.split(local_path)[-1], file)

                except (ConnectionResetError, TimeoutError, ConnectionAbortedError) as err:
                    log.error('Transfer Error. File: {}. {}'.format(local_path, err))
                    print('!--- Transfer Error. File: {}. {}'.format(local_path, err))
                    return 1

        except FileNotFoundError as err:
            log.error('Transfer Error. File: {}. {}'.format(local_path, err))
            print('!--- ERR Transfer error: ' , err)


    def check_ftp_folder(self, connection, path_str):
        """
            The function checks for availability and creates folders for storing the file on the server

            'path_str' contain direct path to the file on the server
        """

        path = path_str.split('/')
        for folder in path:
            if folder not in connection.nlst():
                try:
                    connection.mkd(folder)
                    connection.cwd(folder)
                except Exception as err:
                    print('!-- Folder cannot be created: {}'.format(err))
                    log.error('Folder cannot be created: {}'.format(err))

                    return 1
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

    def run(self):
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

        path = 'test files'
        self.file_list = os.listdir(path)
        self.server_folders_list = ['Folder1', 'Folder1/subfolder1', 'Folder1/subfolder1/subfolder12', 'Folder2', 'Folder3']

        for i in range(11):
            time.sleep(random.randint(1,5))
            tmp_json_data = self.json_template

            tmp_json_data['file']['local_path'] = os.path.abspath(path + '/' + random.choice(self.file_list))
            tmp_json_data['file']['server_path'] = random.choice(self.server_folders_list)

            temp_name = 'data_json' + str(i) + '_' + str(int(random.random()*100)) + '.json'
            with open(temp_name, "w") as write_file:
                json.dump(tmp_json_data, write_file, ensure_ascii=False,)

            os.rename(temp_name, 'files/' + temp_name)


def logger_creator():
    """ Creating a logger for recording """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("logs.log")

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.info("Program started")
    return logger


if __name__ == "__main__":
    log = logger_creator()
#     Uncommit this lines to run the test
#     test_thread = TestGenerator('test')
    main_thread = JsonChecker('main')
#     test_thread.start()
    main_thread.start()
