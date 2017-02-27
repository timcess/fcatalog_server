The FCatalog Server
===================

Проект основан на http://www.xorpd.net/pages/fcatalog.html

FCatalog позволяет хранить на сервере информацию об уже исследованых (разревёршенных) файлах.
На данный момент он поддерживает
* Хранение на сервере сигнатур функций и их автоматическое сопоставление с функциями в новом бинарнике с последующим переименованием
* Выборочный или полный импорт/экспорт структур на сервер
* Все функции и структуры можно разносить по разным базам данных для разных проектов


Requirements
------------

- The server will only run on Linux. Tested on Ubuntu 14.04, Linux Mint 17, Linux Mint 18
- Python >= 3.4
- gcc
- curl (sudo apt-get install curl)

Installation and usage in usual mode
------------

Для установки в обычном режиме используйте

    ./get_deps
    sudo ./install

Тогда для FCatalog будет создан отдельный пользователь с домашней директорией, а для применения любых изменений будет необходима переустановка

Для запуска используйте следующую команду

    sudo ./start.sh

По умолчанию сервер запускается на 127.0.0.1:1337

Для удаления используйте

    sudo ./uninstall

Installation and usage in development mode
------------

Для установки в режиме разработки используйте

    ./get_deps
    sudo ./install develop

В этом случае любые изменения в коде будут применены сразу же после перезапуска сервера.
FCatalog будет установлен в домашнюю директорию пользователя в папку fcatalog\_dev 

Для запуска используйте

    cd ~/fcatalog_dev
    source ufcatalog_env/bin/activate
    cd bin
    ./fcatalog_server 0.0.0.0 1337

Tests
-----

Install pytest:

    pip install pytest

and run:

    py.test
