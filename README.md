# Тестовое задание
Тестовое задание по передаче файлов на FTP сервер согласно конфигурационным файлам с 
использованием многопроцессности и ООП подхода на языке Python.

Автор: Мясников Роман

Email: chyvak357@gmail.com


## Использование

Что бы использовать программу, необходимо в рабочей папке **вместе с файлом "main.py"**  создать папки: "**files**", "**checked**".
Программа ожидает появление конфигурационных файлов формата json в папке "files" и после чтения переносит его в папку "checked".

Что бы запустить тест на передачу 10 файлов раскомментируйте две строчки в начале исполнения кода и измените параметры в шаблоне для вашего FTP сервера.

### Структура конфигурационного файла

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
    

## Как это работает
В начале исполнения программы создаётся основной поток класса **JsonChecker** для проверки наличия конфиг файлов в папке "files" и вызове нового потока для обработки файла и передачи соответствующего файла. 

При поступлении конфиг файла запускается поток класса **FileTransfer** который читает данный из конфиг файла, устанавливает соединение с сервером, загружает нужный файл на сервер, создаёт необходимые директории.

### Недостатки и проблемы

 - Множественные тесты не привели к решению обработки ошибок возникающих  при неожиданном разрыве соединения с ftp сервером. При этом основной продолжит работу в ожидании конфиг файлов.
   
 - Не была реализована проверка целостности передачи файлов. При разрыве  неожиданном закрытии программы, файлы находящиеся в процессе передачи не будут переданы полностью.
   
  - Допущения: считается, что все поля конфиг файла заполнены корректно,  необязательно приведут к подключению.
