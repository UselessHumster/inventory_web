import json


class QuerySet:
    def __init__(self, model, data):
        self.model = model
        self._data = data

    def all(self):
        return QuerySet(self.model, self._data)

    def filter(self, **kwargs):
        def match(item):
            for key, value in kwargs.items():
                if getattr(item, key) != value:
                    return False
            return True

        filtered = [item for item in self._data if match(item)]
        return QuerySet(self.model, filtered)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def first(self):
        return self._data[0] if self._data else None


class Manager:
    def __init__(self, model):
        self.model = model
        self._data = []

    def load(self, raw_data):
        # преобразуем словари в объекты модели
        self._data = [self.model(**item) for item in raw_data]

    def all(self):
        return QuerySet(self.model, self._data)

    def filter(self, **kwargs):
        return self.all().filter(**kwargs)


class Device:
    def __init__(self, type, model, serial, owner):
        self.type = type
        self.model = model
        self.serial_number = serial  # переименовали поле
        self.owner = owner

    def __repr__(self):
        return f"<Device {self.serial_number}>"


class Devices:
    objects = Manager(Device)

def load_data_from_json(file_path):
    data = json.load(open(file_path, 'r'))
    Devices.objects.load(data)

def latin_to_cyrillic(text):
    rules = {
        "shch": "щ",
        "yo": "ё",
        "yu": "ю",
        "ya": "я",
        "zh": "ж",
        "kh": "х",
        "ts": "ц",
        "ch": "ч",
        "sh": "ш",
        "a": "а", "b": "б", "v": "в", "g": "г", "d": "д",
        "e": "е", "z": "з", "i": "и", "y": "й", "k": "к",
        "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
        "r": "р", "s": "с", "t": "т", "u": "у", "f": "ф",
        "h": "х", "c": "к"
    }

    text = text.lower()
    result = ""

    i = 0
    while i < len(text):
        for length in (4, 3, 2, 1):
            chunk = text[i:i+length]
            if chunk in rules:
                result += rules[chunk]
                i += length
                break
        else:
            result += text[i]
            i += 1

    return result.capitalize()