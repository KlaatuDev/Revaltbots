import sqlite3 as sql
import datetime as dt
import traceback
import sys
from enum import Enum
import logging
import logging.handlers

from numpy import full

#dt.datetime.utcfromtimestamp(1692812288).strftime('%Y-%m-%d %H:%M:%S')  Преобразование из юникс формата
class TablesEnum():
    """Класс, хранящий в себе структуру базы данных, именна таблиц и полей, а также их описание.
    Каждый вложенный класс содержит поле value, которе хранит имя(в виде строки) таблицы, которую этот класс представляет. 
    Также каждый класс содержит поля, представляющие имена полей таблицы. Для каждого поля указано, какой тип данных оно имеет в таблицы и может ли быть равным NULL."""
    class CampaigningCandidates():
        """Таблица кандидатов на агитацию."""
        value = 'campaigning_candidates'
        VkId = 'vk_id'
        """ВК ID кандидадата на агитацию. Тип данных - INTEGER. Не может быть равным NULL."""
        TelegramLink = 'telegram_link'
        """Ссылка на телеграм акаунт кандидата. Тип данных - TEXT. Может быть равным NULL."""
        FullName = 'full_name'
        """Полное имя или ник кандидата. Тип данных - TEXT. Не может быть равным NULL."""
        DateAdded = 'date_added'
        """Дата добавления кандидата. Тип данных - DATE. Не может быть равным NULL. 
        По умолчанию, при добавлении кандидата, этому полю присваивается дата в момент добавления (сегодняшняя дата)."""
        WhoAdded = 'who_added'
        """Фио или ник добавившего кандидата. Тип данных - TEXT. Не может быть равным NULL. """
        CooldownDate = 'cooldown_date'
        """Дата, после которой кандидат будет выдаваться на повторную агитацию. Тип данных - DATE. Не может быть равным NULL.
        По умолчанию, при добавлении кандидата, этому полю присваивается дата на день раньше момента добавления (вчерашняя дата)."""
    class Agitations():
        """Таблица агитаций. Хранит текущие и прошедшии неудачные агитации."""
        value = "agitations"
        StartDate = 'start_date'
        """Дата начала агитации. Тип данных - DATE. Не может быть равным NULL. 
        По умолчанию, при начале агитации, этому полю присваивается дата в момент начала агитации (сегодняшняя дата)."""
        EndDate = 'end_date'
        """Дата окончания агитации. Тип данных - DATE. Может быть равным NULL. 
        Пока это поле имеет значение NULL - агитация считается не законченной."""
        VkId = 'vk_id'
        """ВК ID агитируемого. Тип данных - INTEGER. Не может быть равным NULL."""
        Agitator = 'agitator'
        """ФИО или ник агитатора. Тип данных - TEXT. Не может быть равным NULL."""
        BoolResult =  'bool_result'
        """Результат агитации. Тип даннх - INTEGER. Может быть равным NULL.
        Значения: 0 - неудачная агитация, 1 - удачная агитация."""
        ResultDescription = 'result_description'
        """Описание результата агитации. Тип данных - TEXT. Может быть равным NULL."""
    class BlackList():
        value = 'black_list'
        """Чёрный список. Люди из этого списка запрещенны для агитации."""
        VkId = 'vk_id'
        """VkId запрещённые для агитации. Тип данных - INTEGET. Не может быть равным NULL."""
        TelegramLink = 'telegram_link'
        """Ссылка на телеграм. Тип данных - TEXT. Может быть равным NULL."""
        WhoAddedId = 'who_added_id'
        """Id из VipList, добавившего человека в чёрный список. Тип данных - INTEGER. Не может быть равным NULL."""
        Description = 'description'
        """Описание причин добавления в чёрный список. Тип данных - TEXT. Может быть равным NULL."""          
    class VipList():
        """Таблица, хранящая VkId людей, имют повышенные права доступа."""
        value = "vip_list"
        VkId = "vk_id",
        """ВК ID, который имеет повышенный доступ. Тип данных -  INTEGER. Не может быть равным NULL."""
        AccessLevel = "access_level"
        """ Уровень доступа. Тип данных - INTEGER. Не может быть равным NULL."""

class DataBaseManager():
    """Класс, осуществляющий работу с базой данных агитации"""    

    def __init__(self, dbPath : str = "Bot.db", autoCommit : bool = True, logger : logging.Logger = None) -> None:
        """Описание конструктора"""
        self.connection = sql.connect(dbPath)
        self.cursor = sql.Cursor(self.connection) 
        self.autoCommit = autoCommit
        
        if logger == None:#Настройки логгера по умолчанию
            
            self.logger = logging.getLogger("db")
            
            sh = logging.StreamHandler()            
            sh.setFormatter(logging.Formatter("%(asctime)s|%(levelname)s|%(funcName)s:%(lineno)d|%(message)s"))
            sh.setLevel(logging.DEBUG)
            
            fh = logging.handlers.RotatingFileHandler(
                filename="dblogs/dberrorlog.log",
                maxBytes=5242880,
                backupCount=10
                )            
            fh.setFormatter(logging.Formatter("%(asctime)s|%(levelname)s|%(funcName)s:%(lineno)d|%(message)s"))
            fh.setLevel(logging.WARNING)
                        
            self.logger.addHandler(sh)
            self.logger.addHandler(fh)
        else:
            self.logger = logger
        
        pass
    
    
    # Общие функции
    
    def Commit(self):
        try:
            self.connection.commit()
        except sql.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    def TablesNames(self) -> list:
        """Возвращает имена таблиц."""
        try:
            return self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        except sql.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
        return []
    
    def Pragma(self, table : str) -> list[str]:
        """Возвращает информацию о полях таблицы."""
        print(table)
        var = self.cursor
        var1 = var.execute(f"PRAGMA table_info({table})")
        return var1.fetchall()   
    
    
    
    # Функции для работы с кандидатами на агитацию.  
    
    def AddCampaigningCandidates(self, vk_id : list[int]|list[str], full_name : list[str], who_added : list[str], telegram_link : list[str] = None, date_added : list[dt.date]  = None, cooldown_date : list[dt.date]  = None, description : list[str] = None) -> list[int]: # type: ignore
        """Добавляет кандидата на агитацию. 
        Входные аргументы должны быть итерируемыми, одинаковой длинны и быть однородными (содержать элементы только одного типа), 
        либо иметь значение по умолчанию. Возвращает id тех кандидатов, которых нельзя добавить в базу данных
        (причинной может быть нахождение в чёрном списке или иное)."""
        
        
        try:
            iter(vk_id)
            iter(full_name)
            iter(who_added)
        except:
            raise "Входные аргументы должны быть итерируемыми."              
        if not all(len(vk_id) == len(l) for l in [full_name, who_added]):
            raise ValueError("Обязательные аргументы не одинаковой длинны.")
        if not all(all(type(x) == type(l[0]) for x in l[1:]) for l in [full_name, who_added, vk_id]):
                raise ValueError("Обязательные аргументы не однородны.")
        
        
        request = f"""SELECT {TablesEnum.BlackList.VkId} 
                      FROM {TablesEnum.BlackList.value}
                      WHERE {TablesEnum.BlackList.VkId} IN ({','.join([str(i) for i in vk_id])});"""
                      
        try:
            break_id = self.cursor.execute(request).fetchall() # VkId находящиеся в чёрном списке
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на выбор записей")
            self.logger.debug("Ошибка выполнения запроса на выбор записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(i for i in traceback.format_exception(exc_type, exc_value, exc_tb))
        
        # Убираем из входных данных записи находящиеся в чёрном списке и запоминаем их индексы
        indexes = []
        for i in range(len(vk_id)):            
            if vk_id[i] in break_id:
                indexes.append(i)
                vk_id.pop(i)
                full_name.pop(i)
                who_added.pop(i)
        
        addField = {"vk_id" : list(str(x) for x in vk_id), "full_name" : ["'" + i + "'" for i in full_name], "who_added" : ["'" + i + "'" for i in who_added]}
        
        for elem in zip(["telegram_link", "date_added", "cooldown_date", "description"], [telegram_link, date_added, cooldown_date, description], [str, dt.date, dt.date, str]):
            if elem[1] != None:
                [elem[1].pop(i) for i in indexes] # Используем индексы, которые запомнили ранее, чтобы удалить соответствующие элементы из необязательных аргументов
                if len(elem[1]) != len(vk_id):
                    raise ValueError(f"Аргумент {elem[0]} не подходящей длины.")
                if not all( elem[2] == type(i) for i in elem[1]):
                    raise ValueError(f"Аргумент {elem[0]} не однороден.")
                if elem[2] == dt.date:
                    addField.update({elem[0]: [str(i) for i in elem[1]]})#type: ignore
                    continue
                if elem[2] == str:
                    addField.update({elem[0]: ["'" + i + "'" for i in elem[1]]})#type: ignore
                    continue
                addField.update({elem[0]:elem[1]})#type: ignore
        
        
        
        
        request = f"""INSERT or IGNORE INTO {TablesEnum.CampaigningCandidates.value}({str.join(',', list(addField.keys()))}) VALUES {
            str.join(',', 
            [ '('+str.join(',', x)+')' for x in 
            [[row[i] for row in list(addField.values())] for i in range(len( list(addField.values()) [0]))]
            ])
        };"""
        
        try:
            self.cursor.execute(request)#campaigning_candidates
            if self.autoCommit:
                self.connection.commit()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на добавление записей")
            self.logger.debug("Ошибка выполнения запроса на добавление записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(i for i in traceback.format_exception(exc_type, exc_value, exc_tb))
                
        return break_id
    
    def DeleteCampaigningCandidates(self, vk_id : list[int]|list[str], cascade : bool = True):
        """Удаляет кандидатов по их id. Возвращает записи, которые были удалены. 
        Если значение cascade равняется "True", то из таблицы Agitations удаляются все записис с тем же id, кроме успешных."""
        if len(vk_id) < 1:
            raise ValueError("Аргумент vk_id должен иметь длинну 1 или больше.")
        if all(type(i) == int for i in vk_id):
            strVk_id = [str(i) for i in vk_id]
        if all(type(i) == str for i in vk_id):
            strVk_id = vk_id
        else:
            raise ValueError("Аргумент vk_id не однороден или имеет несоответствующий тип.")
        
        try:
            outVar = self.cursor.execute(f"SELECT * FROM {TablesEnum.CampaigningCandidates.value} WHERE vk_id IN ({str.join(',', strVk_id)});").fetchall() # type: ignore
        except:
            self.logger.error("Ошибка выполнения запроса на выбор записей")
            self.logger.debug("Ошибка выполнения запроса на выбор записей", er.args, exc_info=sys.exc_info())
        
        try:
            
            self.cursor.execute(f"DELETE FROM {TablesEnum.CampaigningCandidates.value} WHERE vk_id IN ({str.join(',', strVk_id)});" ) # type: ignore
            if self.autoCommit:
                self.connection.commit()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на удаление записей")
            self.logger.debug("Ошибка выполнения запроса на удаления записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        if cascade:
            try:
                self.cursor.execute(f"DELETE FROM {TablesEnum.Agitations.value} WHERE {TablesEnum.Agitations.VkId} IN ({str.join(', ', strVk_id)}) AND {TablesEnum.Agitations.BoolResult} != 1;")#type:ignore
            except sql.Error as er:
                self.logger.error("Не удалось выполнить каскадное удаление")
                self.logger.debug("Не удалось выполнить каскадное удаление", er.args, exc_info=sys.exc_info())
                # print('Не удалось выполнить каскадное удаление. SQLite error: %s' % (' '.join(er.args)))
                # print("Exception class is: ", er.__class__)
                # print('SQLite traceback: ')
                # exc_type, exc_value, exc_tb = sys.exc_info()
                # print(traceback.format_exception(exc_type, exc_value, exc_tb))
            finally: return outVar#type: ignore
        
        return outVar #type: ignore
    
    def GetCampaigningCandidates(self, count : int|None = None, fields : list[str] = ["*"], filters : dict[str, str] = dict()) -> list:
        """Возвращает кандидатов на агитацию. count - максимально возможное кол-во записей, которое будет возвращено (по умолчанию - все возможные).
        fields - поля, которые будут возвращены. filters - фильтр на выбор записей. Если в качестве фильтра поля нужно указать конкретные значения, то нужно использовать строку вида:
        'IN (val1, val2, val3)'."""
        request = f"SELECT {str.join(',', fields)} FROM {TablesEnum.CampaigningCandidates.value}"
        if len(filters) > 0:
            request += f" WHERE {str.join(' AND ', [i+' '+filters[i] for i in filters])}"
        if count != None and count >= 0:
            request += f" LIMIT {count}"

        result = []
        try:
            result = self.cursor.execute(request).fetchall()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на выбор записей")
            self.logger.debug("Ошибка выполнения запроса на выбор записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
            return []
        
        return result
    
    
    # Функции для работы с агитациями.
    # Скорее всего в функции много лишних преобразований из int в str (как минимум есть лишние преобразования в str связанные с vk_id).
    # Можно подумать как это исправить    
    
    def StartAgitations(self, vk_id: list[int]|list[str], agitators: list[str], endDates : list[dt.date] = None) -> list[str]:
        """Наичнает новые агитации. Аргументы должны быть одной длинны и однородны. Возвращает id тех кандидатов, с которыми сейчас уже ведут агитацию 
        или если id нету в таблице кандидатов. По умолчанию endDates присваивается сегодняшняя дата +3 дня."""
        
        # Вадидация аргументов
        try:
            iter(vk_id)
            iter(agitators)
        except:
            raise ValueError("Аргументы должны быть итерируемыми.")
        if len(vk_id) != len(agitators):
            raise ValueError("Аргументы должны быть одной длинны.")
        if all(type(i) == int for i in vk_id):
            strVk_id = [str(i) for i in vk_id]
        elif all(type(i) == str for i in vk_id):
            strVk_id = vk_id
        else:
            raise ValueError("vk_id имеет несоответствующий тип.")
        if any(type(i) != str for i in agitators):
            raise ValueError("Аргумент agitators имеет несоответствующий тип.")
        if endDates == None:
            endDates = [dt.date.today() + dt.timedelta(days=3)]*len(vk_id)
        else:
            if len(endDates) != len(vk_id):
                raise ValueError("Аргумент endDate имеет не подходящую длинну.")
            if any(type(i) != dt.date for i in endDates):
                raise ValueError("Аргумент endDate имеет не подходящий тип элементов или не однороден.")
            if any(i < dt.date.today() for i in endDates):
                raise ValueError("Дата окончания агитации не может быть в прошлом.")
        
        breake_id = set()
        #добавляем в breake_id людей, которых нету в таблице кандидатов на агитацю. 
        request = f"SELECT vk_id FROM {TablesEnum.CampaigningCandidates.value} WHERE vk_id IN ({str.join(',', strVk_id)});"#type:ignore
        try:
            
            #тут происходит вычитание имеющихся в бд id из id переданных в функцию. Таким образом мы получаем id тех кого нету в таблице кандидатов.
            breake_id = set(strVk_id) - set(str(i[0]) for i in self.cursor.execute(request).fetchall())
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на выбор записей")
            self.logger.debug("Ошибка выполнения запроса на выбор записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        
        # Тут мы добавляем в breake_id кандидатов, новая агитация для которых сейчас не возможна (их cooldown_date позже чем сегодня)
        request = f"""SELECT vk_id FROM {TablesEnum.CampaigningCandidates.value}
                      WHERE {TablesEnum.CampaigningCandidates.CooldownDate} > date('now')
                      AND {TablesEnum.CampaigningCandidates.VkId} IN ({ ','.join( set(strVk_id) - breake_id ) });"""#type:ignore
        try:
            breake_id |= set(str(i[0]) for i in self.cursor.execute(request).fetchall())
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на добавление записей")
            self.logger.debug("Ошибка выполнения запроса на добавление записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
                
        #request = f"INSERT INTO {TablesEnum.Agitations.value}(vk_id, agitator) VALUES"                    #Просто пример как делать INSERT
        result_values = [[strVk_id[i], "'"+agitators[i]+"'", f"'{endDates[i]}'"]  for i in range(len(strVk_id)) if strVk_id[i] not in breake_id]
    
        try:
            if len(result_values) > 0:
                # Вставляем новые записи агитаций, то есть начинаем их 
                # А также Обновляем записи кандидатов, выставляя по умолчание cooldown_date date('now') + 60 дней
                request = f"""INSERT INTO {TablesEnum.Agitations.value}(vk_id, agitator, end_date) VALUES 
                {
                    ','.join( ['(' + ','.join(i) + ')' for i in result_values]) 
                };
                UPDATE {TablesEnum.CampaigningCandidates.value}
                SET {TablesEnum.CampaigningCandidates.CooldownDate} = date('now', '+14 day') 
                WHERE {TablesEnum.CampaigningCandidates.VkId} IN ({','.join([i[0] for i in result_values])});"""
                
                self.cursor.executescript(request)
                if self.autoCommit:
                    self.connection.commit()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на добавление записей")
            self.logger.debug("Ошибка выполнения запроса на добавление записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
            return []

        # try:
        #     if len(result_values) > 0:
        #         self.cursor.execute(f""" UPDATE {TablesEnum.CampaigningCandidates.value}
        #                                  SET {TablesEnum.CampaigningCandidates.CooldownDate} = date('now', '+60 day') 
        #                                  WHERE {TablesEnum.CampaigningCandidates.VkId} IN ({','.join([i[0] for i in result_values])});""")#
        #         if self.autoCommit:
        #             self.connection.commit()
        # except sql.Error as er:
        #     print('SQLite error: %s' % (' '.join(er.args)))
        #     print("Exception class is: ", er.__class__)
        #     print('SQLite traceback: ')
        #     exc_type, exc_value, exc_tb = sys.exc_info()
        #     print(traceback.format_exception(exc_type, exc_value, exc_tb))
        #     return []
        
        return breake_id # type: ignore
    
    def GetAgitations(self, count : int|None = None, fields : list[str] = ['*'], filters : dict[str, str] = dict()) -> list:
        """Возвращает агитации. 
        count - колличество возвращённых записей не будет превышать этого аргумента. 
        fields - список полей которые будут выбраны.
        filters - словарь фильтров. Ключи - поля, значения - ограничения для выбора полей. 
        Примеры: filters = {'vk_id', '> 10'} => vk_id > 10;
                 filters = {'agitator', 'IN (\'name 1\', \'name 2\', \'name 3\')'} => agitator IN (\'name 1\', \'name 2\', \'name 3\')
        """
        
        if len(filters) > 0:
            request = f"""SELECT {str.join(',', fields)} FROM {TablesEnum.Agitations.value} WHERE {str.join(" AND ", [i+' '+filters[i] for i in filters])}"""
        else:
            request = f"""SELECT {str.join(',', fields)} FROM {TablesEnum.Agitations.value}"""
        if type(count) == int and count >= 1:
            request += f" LIMIT {count}"
        
        result = []
        try:
            result = self.cursor.execute(request).fetchall()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на выбор записей")
            self.logger.debug("Ошибка выполнения запроса на выбор записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
            return []
        
        return result
    
    def GetCurrentAgitations(self, count : int|None = None, fields : list[str] = ['*']) -> list:
        """ Возвращает агитации идущие в текущий момент. 
        count - максимальное (но не минимальное!) число агитаций, которе будет возвращено.
        fields - поля (столбцы) которые будут возвращены. """
        request = f"""SELECT {str.join(',', fields)} FROM {TablesEnum.Agitations.value} WHERE {TablesEnum.Agitations.EndDate} > date('now') """  
        if count != None and count >= 0:
            request += f" LIMIT {count}"
        result = []
        try:
            result = self.cursor.execute(request).fetchall()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на выбор записей")
            self.logger.debug("Ошибка выполнения запроса на выбор записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
            return []
        return result
    
    def FailedAgitations (self, vk_id : list[int]|list[str], startDates : list[dt.date], agitators : list[str], resultDescriptions : list[str], endDates : list[dt.date] = None, cooldownDate : list[dt.date] = None): #type:ignore
        """Заканчивает агитации неудачей. Аргументы должны быть одной длинны и однородными."""
        try: 
            (iter(x) for x in [vk_id, startDates, agitators, resultDescriptions])
        except: raise ValueError("Аргументы должны быть итерируемыми.")
        
        if all(len(l) == 0 for l in [vk_id, startDates, agitators, resultDescriptions]):
            return #Если все массивы пустые просто не выполняем функцию
        
        for l in [vk_id, startDates, agitators, resultDescriptions]:
            if any(type(l[0]) != type(i) for i in l[1:]):
                raise ValueError("Массивы аргументов не однородны.")
            if len(l) != len(vk_id):
                raise ValueError("Аргументы не одинаковой длинны.")
        
        if type(vk_id[0]) == int:
            strVk_id = [str(i) for i in vk_id]
        elif type(vk_id[0]) == str:
            strVk_id = vk_id
        else:
            raise ValueError("Аргумент vk_id имеет не соответствющий тип.")
        
        for i in zip([startDates, agitators, resultDescriptions], [dt.date, str, str]):
            if type(i[0][0]) != i[1]:
               raise ValueError("Аргументы имеют неверные типы.")
           
        if endDates == None:
            dEnd = [None]*len(vk_id)
        else:
            if len(vk_id) != len(endDates):#type: ignore
                raise ValueError("Аргумент endDates имеет не подходящую длинну.")
            if any((type(i) != dt.date and i != None) for i in endDates):#type: ignore
                raise ValueError("Элементы endDates имеют не подходящий тип. Подходящие тип элементов endDates: datetime.date.")
            dEnd = endDates
        
        if cooldownDate == None:
            cDate = [None]*len(vk_id)
        else:
            if len(vk_id) != len(cooldownDate):#type: ignore
                raise ValueError("Аргумент cooldownDate имеет не подходящую длинну.")
            if any((type(i) != dt.date and i != None) for i in cooldownDate):#type: ignore
                raise ValueError("Элементы cooldownDate имеют не подходящий тип. Подходящие тип элементов cooldownDate: datetime.date.")
            cDate = cooldownDate
                 
        for i in range(len(vk_id)):
            
            request = f"UPDATE {TablesEnum.Agitations.value} SET "
            if dEnd[i] != None:
                request += f"{TablesEnum.Agitations.EndDate} = '{dEnd[i]}',"

            request += f"""
            {TablesEnum.Agitations.ResultDescription} = '{resultDescriptions[i]}',
            {TablesEnum.Agitations.BoolResult} = 0 WHERE
            {TablesEnum.Agitations.VkId} = {vk_id[i]} AND {TablesEnum.Agitations.StartDate} = '{startDates[i]}' AND {TablesEnum.Agitations.Agitator} = '{agitators[i]}';
            """
            
            if cooldownDate[i] != None:
                request += f""" UPDATE {TablesEnum.CampaigningCandidates.value} SET 
                {TablesEnum.CampaigningCandidates.CooldownDate} = '{cooldownDate[i]}' WHERE
                {TablesEnum.Agitations.VkId} = {vk_id[i]};"""
            
            try:
                self.cursor.executescript(request)
            except sql.Error as er:
                self.logger.error("Ошибка выполнения запроса на обновление записей")
                self.logger.debug("Ошибка выполнения запроса на обновление записей", er.args, exc_info=sys.exc_info())
                # print('SQLite error: %s' % (' '.join(er.args)))
                # print("Exception class is: ", er.__class__)
                # print('SQLite traceback: ')
                # exc_type, exc_value, exc_tb = sys.exc_info()
                # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        if self.autoCommit:
            self.connection.commit()

        pass
    
    def SuccesAgitations (self, vk_id : list[int]|list[str], startDates : list[dt.date], agitators : list[str], resultDescriptions : list[str], endDates : list[dt.date] = None, cooldownDate : list[dt.date] = None, cascade : bool = True): #type:ignore
        """Заканчивает агитации успехом. Аргументы должны быть одной длинны и однородными. 
        Если аргумент "cascade" равняется "True", то из БД будет удалён успешно сагитированный кандидат, а также будут удалены все неуспешные агитации с ним."""
        try: 
            (iter(x) for x in [vk_id, startDates, agitators, resultDescriptions])
        except: raise ValueError("Аргументы должны быть итерируемыми.")
        
        if all(len(l) == 0 for l in [vk_id, startDates, agitators, resultDescriptions]):
            return #Если все массивы пустые просто не выполняем функцию
        
        for l in [vk_id, startDates, agitators, resultDescriptions]:
            if any(type(l[0]) != type(i) for i in l[1:]):
                raise ValueError("Массивы аргументов не однородны.")
            if len(l) != len(vk_id):
                raise ValueError("Аргументы не одинаковой длинны.")
        
        if type(vk_id[0]) == int:
            strVk_id = [str(i) for i in vk_id]
        elif type(vk_id[0]) == str:
            strVk_id = vk_id
        else:
            raise ValueError("Аргумент vk_id имеет не соответствющий тип.")
        
        for i in zip([startDates, agitators, resultDescriptions], [dt.date, str, str]):
            if type(i[0][0]) != i[1]:
               raise ValueError("Аргументы имеют неверные типы.")
        
        if endDates == None:
            dEnd = [None]*len(vk_id)
        else:
            if len(vk_id) != len(endDates):#type: ignore
                raise ValueError("Аргумент endDates имеет не подходящую длинну.")
            if any((type(i) != dt.date and i != None) for i in endDates):#type: ignore
                raise ValueError("Аргумент endDates не однороден.")
            dEnd = endDates
        
        if cooldownDate == None:
            cDate = [None]*len(vk_id)
        else:
            if len(vk_id) != len(cooldownDate):#type: ignore
                raise ValueError("Аргумент cooldownDate имеет не подходящую длинну.")
            if any((type(i) != dt.date and i != None) for i in cooldownDate):#type: ignore
                raise ValueError("Элементы cooldownDate имеют не подходящий тип. Подходящие тип элементов cooldownDate: datetime.date.")
            cDate = cooldownDate
        
        #При разрешении каскадного удаления - удаляем все записи связанные с успешно заагитированным человеком, оставляя только запись о том, что он успешно сагитирован
        if cascade:
                self.DeleteCampaigningCandidates(strVk_id, cascade)
        
        # Выполняем обновление записей
        for i in range(len(vk_id)):
            request = f"UPDATE {TablesEnum.Agitations.value} SET "
            if dEnd[i] != None:
                request += f"{TablesEnum.Agitations.EndDate} = '{dEnd[i]}',"
            
            request += f"""                
            {TablesEnum.Agitations.ResultDescription} = '{resultDescriptions[i]}',
            {TablesEnum.Agitations.BoolResult} = 1 WHERE
            {TablesEnum.Agitations.VkId} = {vk_id[i]} AND {TablesEnum.Agitations.StartDate} = '{startDates[i]}' AND {TablesEnum.Agitations.Agitator} = '{agitators[i]}';
            """
            
            if cooldownDate[i] != None and not cascade:
                request += f""" UPDATE {TablesEnum.CampaigningCandidates.value} SET 
                {TablesEnum.CampaigningCandidates.CooldownDate} = '{cooldownDate[i]}' WHERE
                {TablesEnum.Agitations.VkId} = {vk_id[i]};"""  
                        
            try:
                self.cursor.executescript(request)
            except sql.Error as er:
                self.logger.error("Ошибка выполнения запроса на обновление записей")
                self.logger.debug("Ошибка выполнения запроса на обновление записей", er.args, exc_info=sys.exc_info())
                # print('SQLite error: %s' % (' '.join(er.args)))
                # print("Exception class is: ", er.__class__)
                # print('SQLite traceback: ')
                # exc_type, exc_value, exc_tb = sys.exc_info()
                # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        if self.autoCommit:
            self.connection.commit()

        pass
    
    
    #Функции работы с чёрным списком.
    
    def AddInBLackList(self, vk_id : list[str]|list[int], whoAddedIds : list[str]|list[int], descriptions : list[str], telegramLink : list[str] = None):#type:ignore
        try: 
            (iter(x) for x in [vk_id, whoAddedIds, descriptions])
        except: raise ValueError("Аргументы должны быть итерируемыми.")
        for l in [vk_id, whoAddedIds, descriptions]:
            if any(type(l[0]) != type(i) for i in l[1:]):
                raise ValueError("Массивы аргументов не однородны.")
            if len(l) != len(vk_id):
                raise ValueError("Аргументы не одинаковой длинны.")
        
        if type(vk_id[0]) == int:
            strVk_id = [str(i) for i in vk_id]
        elif type(vk_id[0]) == str:
            strVk_id = vk_id
        
        if set(strVk_id) != set(i[0] for i in self.cursor.execute(f"SELECT {TablesEnum.VipList.VkId} FROM {TablesEnum.VipList.value} WHERE {TablesEnum.VipList.VkId} IN ({str.join(',', strVk_id)});").fetchall() ):#type:ignore
            raise ValueError(" Не все значение whoAddedIds находятся в vipList.")
        
        fields = f"{TablesEnum.BlackList.VkId}, {TablesEnum.BlackList.WhoAddedId}, {TablesEnum.BlackList.Description}"
        
        if telegramLink != None:
            fields += f", {TablesEnum.BlackList.TelegramLink}"
        
        fields = "("+fields+")"
        request = f"""INSERT INTO {TablesEnum.BlackList.value}{fields} VALUES
        {
            str.join(',', 
            [ '('+str.join(',', x)+')' for x in 
            [[row[i] for row in [strVk_id, whoAddedIds, descriptions, telegramLink]] for i in range(len(strVk_id))] 
            ])
        };"""
        
        try:
            self.cursor.execute(request)
            if self.autoCommit:
                self.connection.commit()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на добавление записей")
            self.logger.debug("Ошибка выполнения запроса на добавление записей", er.args, exc_info=sys.exc_info())
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        pass
    
    def DeleteFromBlackList(self, vk_id : list[str]|list[int]):
        
        if len(vk_id) < 1:
            raise ValueError("Аргумент vk_id должен иметь длинну 1 или больше.")
        if all(type(i) == int for i in vk_id):
            strVk_id = [str(i) for i in vk_id]
        if all(type(i) == str for i in vk_id):
            strVk_id = vk_id
        else:
            raise ValueError("Аргумент vk_id не однороден или имеет несоответствующий тип.")
        
        request = f"DELETE FROM {TablesEnum.BlackList.value} WHERE {TablesEnum.BlackList.VkId} IN ({str.join(',', strVk_id)});"#type:ignore
        
        try:
            self.cursor.execute(request)
            if self.autoCommit:
                self.connection.commit()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на удаление")
            self.logger.debug("Ошибка выполнения запроса на удаление", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        pass
    
    
    # Функция работы с vip списком
    
    def AddInVipList(self, vk_id : list[str]|list[int], accessLevel : list[int]):#type:ignore
        
        #Блок валидации аргументов и приведения типов
        try: 
            (iter(x) for x in [vk_id, accessLevel])
        except: raise ValueError("Аргументы должны быть итерируемыми.")
        for l in [vk_id, accessLevel]:
            if any(type(l[0]) != type(i) for i in l[1:]):
                raise ValueError("Массивы аргументов не однородны.")
            if len(l) != len(vk_id):
                raise ValueError("Аргументы не одинаковой длинны.")
        
        if type(accessLevel[0]) == int:
            strAccess_level = [str(i) for i in vk_id]
        else:
            raise ValueError("accessLevel имеет не подходящий тип.")
        
        if type(vk_id[0]) == int:
            strVk_id = [str(i) for i in vk_id]
        elif type(vk_id[0]) == str:
            strVk_id = vk_id
        else:
            raise ValueError("vk_id имеет не подходящий тип.")
        #Конец блока
        
        request = f"""INSERT INTO {TablesEnum.VipList.value}({TablesEnum.VipList.VkId}, {TablesEnum.VipList.AccessLevel}) VALUES
        {
            str.join(',', 
            [ '('+str.join(',', x)+')' for x in 
            [[row[i] for row in [strVk_id, strAccess_level]] for i in range(len(strVk_id))]
            ])
        };"""
        
        try:
            self.cursor.execute(request)
            if self.autoCommit:
                self.connection.commit()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на добавление записей")
            self.logger.debug("Ошибка выполнения запроса на добавление записей", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        pass
    
    def DeleteFromVipList(self, vk_id : list[str]|list[int]):
        
        if len(vk_id) < 1:
            raise ValueError("Аргумент vk_id должен иметь длинну 1 или больше.")
        if all(type(i) == int for i in vk_id):
            strVk_id = [str(i) for i in vk_id]
        if all(type(i) == str for i in vk_id):
            strVk_id = vk_id
        else:
            raise ValueError("Аргумент vk_id не однороден или имеет несоответствующий тип.")
        
        request = f"DELETE FROM {TablesEnum.VipList.value} WHERE {TablesEnum.VipList.VkId} IN ({str.join(',', strVk_id)});"#type:ignore
        
        try:
            self.cursor.execute(request)
            if self.autoCommit:
                self.connection.commit()
        except sql.Error as er:
            self.logger.error("Ошибка выполнения запроса на удаление")
            self.logger.debug("Ошибка выполнения запроса на удаление", er.args, exc_info=sys.exc_info())
            # print('SQLite error: %s' % (' '.join(er.args)))
            # print("Exception class is: ", er.__class__)
            # print('SQLite traceback: ')
            # exc_type, exc_value, exc_tb = sys.exc_info()
            # print(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        pass
    