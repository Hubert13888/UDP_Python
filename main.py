import socket
import time


SERVER_PORT = 6666
CLIENT_PORT = 6667
SERVER_IP = "localhost"
CLIENT_IP = "localhost"

"""
W funkcji main wybieramy, czy aplikacja ma działać po stronie klienta, czy serwera
"""

def main():
    state = input("1 - serwer, 2 - klient\t\t")
    if state == '1':
        server()
    if state == '2':
        client()


"""
Funkcja isNumber sprawdza czy dana zmienna jest typu float
"""

def isNumber(val):
    try:
        wart = float(val)
        return True
    except ValueError:
        return False


"""
Funkcja isIntNumber sprawdza czy dana zmienna jest typu int
"""

def isIntNumber(val):
    try:
        wart = int(val)
        return True
    except ValueError:
        return False


"""
Funkcja inputNumber żąda wpisania poprawnej wartości numerycznej. Dopóki takowa nie
zostanie wprowadzona to program działać będzie w pętli i wyświetlać komunikat błędu
"""

def inputNumber(text):
    powtarzaj = True
    while powtarzaj:
        wprowadzona = input(text)
        if isNumber(wprowadzona):
            powtarzaj = False
        else:
            print("To nie jest poprawna liczba!")
    return wprowadzona


"""
Funkcja inputIntNumber żąda wpisania poprawnej wartości typu int. Dopóki takowa nie
zostanie wprowadzona to program działać będzie w pętli i wyświetlać komunikaty błędów
"""

def inputIntNumber(text):
    powtarzaj = True
    while powtarzaj:
        wprowadzona = input(text)
        if isIntNumber(wprowadzona):
            if int(wprowadzona) >= 0:
                powtarzaj = False
            else:
                print("Liczba musi być dodatnia.")
        else:
            print("To nie jest poprawna liczba!")
    return wprowadzona


"""
Wynikiem funkcji silnia jest silnie z wartości val
"""
def silnia(val):
    i = 1
    while val > 0:
        i = val * i
        val = val - 1
    return i


"""
Funkcja parse_message wyciąga wszystkie argumenty z pobranego żądania typu string
"""
def parse_message(string):
    split_str = string.split('%')
    arguments = dict()
    for i in range(4):
        args = split_str[i].split(':')
        arguments[args[0]] = args[1]
    return arguments


"""
Funkcja parse_series_of_messages dodaje do tablicy asocjacyjnej kolejne wartości argumentów żądania
omijając przy tym już wcześniej wyciągnięte pola: ID, ZC i NS
"""

def parse_series_of_messages(data):
    all_arguments = dict()
    for i in data[0]:
        all_arguments[i] = data[0][i]

    for i in range(1, len(data)):
        for x in data[i]:
            if (x != "ID") & (x != "ZC") & (x != "NS"):
                all_arguments[x] = data[i][x]

    return all_arguments


"""
Funkcja wait_for_messages zajmuje się nasłuchiwaniem portu do którego mają zostać wysłane dane.
W funkcji tej argumenty zostaną sparsowane do tablicy asocjacyjnej przygotowanej do dalszych działań
"""

def wait_for_messages(sock):
    waiting_for_all_data = True
    currently_processed_data = []
    address = 0
    while waiting_for_all_data:
        data, address = sock.recvfrom(1024)
        parsed = parse_message(data.decode())
        currently_processed_data.append(parsed)
        if parsed["NS"] == '0':
            waiting_for_all_data = False
    all_arguments = parse_series_of_messages(currently_processed_data)
    return all_arguments, address


"""
Funkcją server_process_message serwer działa na argumentach, wykonuuje operacje oraz zwraca odpowiedź do klienta
"""

def server_process_message(data, session_id, current_operation_id, history):
    all_arguments = data
    save_in_history = True

    strings_to_send = []
    string_to_save_in_history = []
    basic_string = "ID:" + str(session_id) + "%"
    basic_string += "ZC:" + str(int(time.time() * 1000)) + "%"

    # Operacja pobierzPrzezOperację polega na wyciągnięciu z historii operacji wszystkich operacji o podanym ID, które
    # klient kazał wykonać serwerowi podczas swojej sesji

    if all_arguments["OP"] == "pobierzPrzezOperacje":
        save_in_history = False
        number = all_arguments["L1"]
        found = False
        for i in history:
            parsed_array = []
            for x in i:
                parsed_array.append(parse_message(x))
            parsed = parse_series_of_messages(parsed_array)

            if parsed["IDO"] == number:
                found = True
                to_return = parsed
                break
        if found:
            ID_info = False
            ZC_info = False
            for i in to_return:
                if i == "ID":
                    ID_info = to_return[i]
                elif i == "ZC":
                    ZC_info = to_return[i]
            if ID_info == all_arguments["ID"]:
                recreated_basic_string = "ID:" + ID_info + "%ZC:" + ZC_info + "%"
                number_of_args = len(to_return) - 4
                print(to_return)
                for i in to_return:
                    if (i == "ID") | (i == "ZC") | (i == "NS"):
                        pass
                    else:
                        strings_to_send.append(recreated_basic_string + "NS:" + str(number_of_args) + "%" + i + ":" + to_return[i] + "%")
                        number_of_args -= 1
            else:
                strings_to_send.append(basic_string + "NS:" + str(2) + "%" + "ST:nieMaszDostepu%")
                strings_to_send.append(basic_string + "NS:" + str(1) + "%" + "OP:pobierzPrzezOperacje%")
                strings_to_send.append(basic_string + "NS:" + str(0) + "%" + "L1:" + str(number) + "%")
        else:
            strings_to_send.append(basic_string + "NS:" + str(2) + "%" + "ST:nieIstniejeOperacja%")
            strings_to_send.append(basic_string + "NS:" + str(1) + "%" + "OP:pobierzPrzezOperacje%")
            strings_to_send.append(basic_string + "NS:" + str(0) + "%" + "L1:" + str(number) + "%")

    # Operacja pobierzPrzezOperację polega na wyciągnięciu z historii operacji
    # wszystkich operacji o numerze sesji równym z numerem sesji klienta

    elif all_arguments["OP"] == "pobierzCalaHistorie":
        save_in_history = False
        session_number = all_arguments["ID"]
        all_to_return = []

        for i in history:
            parsed_array = []
            for x in i:
                parsed_array.append(parse_message(x))
            parsed = parse_series_of_messages(parsed_array)

            if parsed["ID"] == session_number:
                all_to_return.append(parsed)

        all_counter = len(all_to_return) - 1

        for i in all_to_return:
            ID_info = False
            ZC_info = False
            for x in i:
                if x == "ID":
                    ID_info = i[x]
                elif x == "ZC":
                    ZC_info = i[x]

            recreated_basic_string = "ID:" + ID_info + "%ZC:" + ZC_info + "%"
            number_of_args = len(i) - 3
            print(all_to_return)
            for x in i:
                if (x == "ID") | (x == "ZC") | (x == "NS"):
                    pass
                else:
                    strings_to_send.append(recreated_basic_string + "NS:" + str(number_of_args) + "%" + x + ":" + i[x] + "%")
                    number_of_args -= 1
            strings_to_send.append(recreated_basic_string + "NS:" + str(number_of_args) + "%NSP:" + str(all_counter) + "%")

            all_counter -= 1
        if len(all_to_return) == 0:
            strings_to_send.append(basic_string + "NS:" + str(1) + "%ST:pustaHistoria%")
            strings_to_send.append(basic_string + "NS:" + str(0) + "%OP:pobierzCalaHistorie%")

    # W tym bloku kodu zostaną wykonane działanie matematyczne na argumentach L1, L2

    else:
        lp = 0
        status = "poprawne"
        result = 'null'
        if all_arguments["OP"] == "dodawanie":
            result = float(all_arguments["L1"]) + float(all_arguments["L2"])
            lp = 5
        elif all_arguments["OP"] == "odejmowanie":
            result = float(all_arguments["L1"]) - float(all_arguments["L2"])
            lp = 5
        elif all_arguments["OP"] == "mnozenie":
            result = float(all_arguments["L1"]) * float(all_arguments["L2"])
            lp = 5
        elif all_arguments["OP"] == "dzielenie":
            if float(all_arguments["L2"]) == 0:
                status = "dzieleniePrzezZero"
                lp = 3
            else:
                result = float(all_arguments["L1"]) / float(all_arguments["L2"])
                lp = 5
        elif all_arguments["OP"] == "silnia":
            result = silnia(int(all_arguments["L1"]))
            lp = 4

        strings_to_send.append(basic_string + "NS:" + str(lp) + "%" + "L1:" + str(all_arguments["L1"]) + "%")
        lp -= 1
        if "L2" in all_arguments:
            strings_to_send.append(basic_string + "NS:" + str(lp) + "%" + "L2:" + str(all_arguments["L2"]) + "%")
            lp -= 1
        strings_to_send.append(basic_string + "NS:" + str(lp) + "%" + "IDO:" + str(current_operation_id) + "%")
        lp -= 1
        strings_to_send.append(basic_string + "NS:" + str(lp) + "%" + "ST:" + status + "%")
        lp -= 1
        strings_to_send.append(basic_string + "NS:" + str(lp) + "%" + "OP:" + all_arguments["OP"] + "%")
        lp -= 1
        if status == "poprawne":
            strings_to_send.append(basic_string + "NS:" + str(lp) + "%" + "RES:" + str(result) + "%")
            lp -= 1

        string_to_save_in_history = strings_to_send[:]
        if "L2" in all_arguments:
            del strings_to_send[0:2]
        else:
            del strings_to_send[0:1]

    return strings_to_send, save_in_history, string_to_save_in_history


"""
Funkcją server kompletuje wszystkie operacje serwerowe, pobiera dane oraz wysyła odpowiedź do klienta
"""


def server():
    history = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))

    session_counter = 0
    operation_counter = 0

    while True:
        print("Oczekiwanie...")

        all_arguments, address = wait_for_messages(sock)

        print(all_arguments)

        if all_arguments["ID"] == "null":
            session_counter += 1

        sent_message, save_in_history, save_in_history_string = server_process_message(all_arguments, session_counter, operation_counter, history)

        if save_in_history:
            history.append(save_in_history_string)
            operation_counter += 1

        for i in sent_message:
            print("Wyslane " + i)
            sent = sock.sendto(i.encode(), address)


"""
Funkcją generate_client_message skleja żadanie, które ma zostać wysłane do serwera, korzystając z wybranych przez niego opcji
"""


def generate_client_message(session_id, operation, *arguments):
    strings_to_send = []
    basic_string = "ID:" + session_id + "%"
    basic_string += "ZC:" + str(int(time.time() * 1000)) + "%"

    if (operation == "mnozenie") | (operation == "dzielenie") | (operation == "dodawanie") | (operation == "odejmowanie"):
        strings_to_send.append(basic_string + "NS:" + str(3) + "%" + "ST:null%")
        strings_to_send.append(basic_string + "NS:" + str(2) + "%" + "OP:" + operation + "%")
        strings_to_send.append(basic_string + "NS:" + str(1) + "%" + "L1:" + str(arguments[0]) + "%")
        strings_to_send.append(basic_string + "NS:" + str(0) + "%" + "L2:" + str(arguments[1]) + "%")
    elif (operation == "silnia") | (operation == "pobierzPrzezOperacje"):
        strings_to_send.append(basic_string + "NS:" + str(2) + "%" + "ST:null%")
        strings_to_send.append(basic_string + "NS:" + str(1) + "%" + "OP:" + operation + "%")
        strings_to_send.append(basic_string + "NS:" + str(0) + "%" + "L1:" + str(arguments[0]) + "%")
    elif (operation == "pobierzCalaHistorie"):
        strings_to_send.append(basic_string + "NS:" + str(1) + "%" + "ST:null%")
        strings_to_send.append(basic_string + "NS:" + str(0) + "%" + "OP:" + operation + "%")
    else:
        print("zla operacja")

    return strings_to_send


"""
Funkcja client tworzy socket, połączenie z danym portem na które wysyła wiadomość, zawiera też interfejs dzięki któremu
użytkownik może łatwo wybrać operacje do wykonania i wysłać żądanie. Następnie czeka na odpowiedź i wyświetla komunikat
użytkownikowi
"""


def client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, CLIENT_PORT))
    session_id = "null"
    val1 = ""
    val2 = ""
    while True:
        print("\n\n1 - mnozenie\n2 - dzielenie\n3 - odejmowanie"
              "\n4 - dodawanie\n5 - silnia\n6 - odczytaj operacje wedlug id"
              "\n7 - odczytaj cala historie")
        num_chosen = input("Jaka operacje chcesz wykonac?\t\t")
        wyjsc = True
        inpt = "first"

        while wyjsc:
            if inpt == "error":
                print("Nieznana operacja")
                num_chosen = input("Jaka operacje chcesz wykonac?\t\t")

            if num_chosen == '1':
                inpt = "mnozenie"
            elif num_chosen == '2':
                inpt = "dzielenie"
            elif num_chosen == '3':
                inpt = "odejmowanie"
            elif num_chosen == '4':
                inpt = "dodawanie"
            elif num_chosen == '5':
                inpt = "silnia"
            elif num_chosen == '6':
                inpt = "pobierzPrzezOperacje"
            elif num_chosen == '7':
                inpt = "pobierzCalaHistorie"
            else:
                inpt = "error"

            if inpt != "error":
                wyjsc = False

        asked_for_history = False

        if (inpt == "mnozenie") | (inpt == "dzielenie") | (inpt == "odejmowanie") | (inpt == "dodawanie"):
            val1 = inputNumber("Podaj liczbe pierwsza\t\t")
            val2 = inputNumber("Podaj liczbe druga\t\t")
            sent_message = generate_client_message(session_id, inpt, val1, val2)
        elif (inpt == "silnia") | (inpt == "pobierzPrzezOperacje"):
            val1 = inputIntNumber("Podaj wartosc\t\t")
            sent_message = generate_client_message(session_id, inpt, val1)
        elif inpt == "pobierzCalaHistorie":
            sent_message = generate_client_message(session_id, inpt)

        if (inpt == "pobierzCalaHistorie") | (inpt == "pobierzPrzezOperacje"):
            asked_for_history = True

        for i in sent_message:
            sent = sock.sendto(i.encode(), (SERVER_IP, SERVER_PORT))

        wait_for_more = True
        while wait_for_more:
            all_arguments, address = wait_for_messages(sock)

            session_id = all_arguments["ID"]

            print(all_arguments)

            interpret_client_data(all_arguments, asked_for_history, val1, val2)

            if "NSP" in all_arguments:
                if all_arguments["NSP"] == '0':
                    wait_for_more = False
                    asked_for_history = False
            else:
                wait_for_more = False
                asked_for_history = False


"""
Funkcja interpret_client_data zajmuje się interpretacją odpowidzi wysłaniej klientowi przez serwer. Wyświetla
wynik, gdy nie ma błędu. W przeciwnym wypadku interpretuje błąd z pola ST i wyświetla czytelny komunikat użytkownikowi
"""


def interpret_client_data(data, have_values, val1, val2):
    if have_values:
        if data["ST"] == "poprawne":
            if data["OP"] == "mnozenie":
                print(data["L1"] + " * " + data["L2"] + " = " + data["RES"])
            elif data["OP"] == "dzielenie":
                print(data["L1"] + " / " + data["L2"] + " = " + data["RES"])
            elif data["OP"] == "dodawanie":
                print(data["L1"] + " + " + data["L2"] + " = " + data["RES"])
            elif data["OP"] == "odejmowanie":
                print(data["L1"] + " - " + data["L2"] + " = " + data["RES"])
            elif data["OP"] == "silnia":
                print(data["L1"] + "! = " + data["RES"])
        else:
            if data["ST"] == "dzieleniePrzezZero":
                print("Nie wolno dzielić przez zero!")
            elif data["ST"] == "nieMaszDostepu":
                print("Nie masz dostepu")
            elif data["ST"] == "nieIstniejeOperacja":
                print("Nie istnieje taka operacja o ID: " + data["L1"])
            elif data["ST"] == "pustaHistoria":
                print("Historia jest pusta")
    else:
        if data["ST"] == "poprawne":
            if data["OP"] == "mnozenie":
                print(val1 + " * " + val2 + " = " + data["RES"])
            elif data["OP"] == "dzielenie":
                print(val1 + " / " + val2 + " = " + data["RES"])
            elif data["OP"] == "dodawanie":
                print(val1 + " + " + val2 + " = " + data["RES"])
            elif data["OP"] == "odejmowanie":
                print(val1 + " - " + val2 + " = " + data["RES"])
            elif data["OP"] == "silnia":
                print(val1 + "! = " + data["RES"])
        else:
            if data["ST"] == "dzieleniePrzezZero":
                print("Nie wolno dzielić przez zero!")
            elif data["ST"] == "nieMaszDostepu":
                print("Nie masz dostepu")
            elif data["ST"] == "nieIstniejeOperacja":
                print("Nie istnieje taka operacja o ID: " + val1)
            elif data["ST"] == "pustaHistoria":
                print("Historia jest pusta")


main()