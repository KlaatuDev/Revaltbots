from concurrent.futures import thread
from operator import inv
#from email import message
#import errno
from tracemalloc import stop
import datetime
from turtle import forward
from typing import Literal
from requests import session
import RASqliteDataBaseManager as db
import vk_api.vk_api as vkApi
import json
from datetime import datetime as dt
import time
# from vk_api.longpoll import VkLongPoll, VkEventType, VkLongpollMode 
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


import threading
import re
import logging as lg
import logging.config




class Answer:
    """Стандартизированный ответ функций-ответов. Пока что имеет только два поля."""
    def __init__(self, message : str, fwd_messages = []):
      self.message = message
      self.fwd_messages = fwd_messages
      #self.reply_to = reply_to
      pass  
  
class AgitBot:
  
 
  def __init__(self, dbPath : str = "Bot.db", filenameInit : str = "BotInitializeData.json", filenameLoggerInit : str = "LoggerConfig.json"):
    
    self.MAIN_CHAT_ID = 3
    self.AGIT_CHAT_ID = 6  #Для настоящего агит. чата: 4
    
    self.stopFlag = False
    self.party = []
    
    try:
      with open(filenameLoggerInit) as json_file:
        data = json.load(json_file)
        logging.config.dictConfig(data)
        self.logger = lg.getLogger('bot')  
    except:
      raise "Ошибка при попытке чтения файла инициализации логера ошибок."
     
    #self.dbManager = db.DataBaseManager(dbPath, logger=lg.getLogger('db'))#Инициализируем базу данных
        
    try:
      with open(filenameInit) as json_file:
          data = json.load(json_file)
          self.session = vkApi.VkApi(token = data["AccessToken"])
          self.waitTime = data["WaitTime"]
          self.groupId = data["GroupId"]
    except:
      raise "Ошибка при попытке чтения основного файла инициализации."
        
    
    self.mainLoop = threading.Thread(target=self.MainLoop, args=[dbPath,],  daemon = True) 
    self.timersLoop = threading.Thread(target=self.TimersLoop, args=[dbPath,],  daemon = True) 
    pass

  def MainLoop(self, dbPath):
    """Главный цикл бота, в котором обрабатываются поступающие события бота. Автоматически запускается при начале работы бота."""
    lp = VkBotLongPoll(self.session, self.groupId, self.waitTime)
    #print(lp.mode)
    vk = self.session.get_api()
    self.dbManager = db.DataBaseManager(dbPath, logger=lg.getLogger('db'))#Инициализируем базу данных

    # for i in range(0,11,1):
    #   try:
    #     inVk = self.session.method("messages.getConversationMembers", {"peer_id" : 2e9 + i})
    #     print(f"Имя чата {inVk['groups'][0]['name']}")
    #   except Exception as ex:
    #     print(ex)
    
    # for i in range(1,10,1):
    #   try:
    #     inVk = self.session.method("messages.getConversationMembers", {"peer_id" : 2e9+i})
    #     print(f"{i}: Имя чата {inVk['groups'][0]['name']} {len(inVk['items'])}")      
    #   except Exception as ex:
    #     print(ex)  
      
      
    # a = vk.messages.getConversations()
    # for i in a['items']:
    #   rsltstr = f"Тип: {i['conversation']['peer']['type']} Id:{i['conversation']['peer']['id']}"
    #   if i['conversation']['peer']['type'] == 'chat':
    #     rsltstr += f" Имя чата: {i['conversation']['chat_settings']['title']}"
    #   print(rsltstr)
    
    # a = "https://vk.com/paoan"
    # print(a[15:])
    
    # i = vk.users.get(user_ids = "paoan")
    # print(i)
    while not self.stopFlag:
      try:
        for event in lp.listen():          
          if event.type ==  VkBotEventType.MESSAGE_NEW:
          #Слушаем longpoll, если пришло сообщение то:	
            if event.chat_id == self.MAIN_CHAT_ID:
              if 'action' in event.obj.message.keys():
                if event.obj.message['action']['type'] == 'chat_kick_user':
                  i = 0
                  
                  while self.party[i] != event.obj.message['action']['member_id']:    i = i+1
                  else:  self.party.pop(i)                      
                  
                  self.logger.debug("Исключён " + str(event.obj.message['action']['member_id']))
                elif event.obj.message['action']['type'] == 'chat_invite_user':
                  self.party.append( event.obj.message['action']['member_id'] )
                  curAg = self.dbManager.GetAgitations(
                    count=1,
                    fields=[db.TablesEnum.Agitations.StartDate, db.TablesEnum.Agitations.Agitator],
                    filters= {
                      db.TablesEnum.Agitations.BoolResult : " = NULL",
                      db.TablesEnum.Agitations.VkId : " = "+str(event.obj.message['action']['member_id'])
                      }
                    )                      
                  if curAg != []:
                    self.dbManager.SuccesAgitations(
                      vk_id = [event.obj.message['action']['member_id'], ],
                      startDates = [datetime.date.fromisoformat(curAg[0]), ],
                      agitators = [curAg[1], ]
                    )
            else:
              
              #Проверяем наличие команд в сообщении
              answ = self.ChekCommands(event.obj.message, vk)
              
              if answ != None:
                if event.from_user: #Если написали в ЛС    
       
                  vk.messages.send( #Отправляем сообщение
                    user_id=event.obj.message['peer_id'],
                    random_id = int(time.time()*1e6),
                    message=answ.message#,
                    #forward_messages = answ.fwd_messages
                    #guid = int(time.time()*1e6)
                    #reply_to = answ.reply_to Боты не могут отвечать на сообщения
                  )            
                elif event.from_chat: #Если написали в беседе
                                  
                  vk.messages.send( #Отправляем собщение
                    chat_id = event.obj.message['peer_id']-2e9,
                    random_id = int(time.time()*1e6),
                    message = answ.message,
                    forward_messages = answ.fwd_messages
                    #guid = int(time.time()*1e6)
                    
                    #reply_to = answ.reply_to Боты не могут отвечать на сообщения
                  )  
          if self.stopFlag:
            
            vk.messages.send( #Отправляем собщение
                    chat_id = self.AGIT_CHAT_ID,
                    random_id = int(time.time()*1e6),
                    message = "Завершение работы бота."
                    #forward_messages = answ.fwd_messages
                    #guid = int(time.time()*1e6)
                    
                    #reply_to = answ.reply_to Боты не могут отвечать на сообщения
                  )  
            
            break
      except vkApi.VkApiError as er:
        self.logger.warning(er)
      except Exception as ex:
        self.logger.exception(ex)
          
  def Start(self):
    """Запустить бота в паралельной нити."""    
    
    
    inVk = self.session.method("messages.getConversationMembers", {"peer_id" : 2e9 + self.MAIN_CHAT_ID})
    self.logger.debug(f"Запуск бота")
    for j in inVk['items']:        
      self.party.append(j["member_id"])
    
    self.mainLoop.start()
    self.timersLoop.start()
    
    try:
      self.session.method("messages.send", {"chat_id" : self.AGIT_CHAT_ID, "random_id" : int(time.time()*1e6), "message" : "Запуск бота."})
    except vkApi.ApiError as er:
      self.logger.warning("Не удалось отправить сообщение о начале работы бота.")
    except Exception as ex:
      self.logger.exception(ex)
    

  def End(self):
    """Безопасно закончить работу бота."""
    
    self.logger.debug("Начало завершения работы бота.")    
    self.stopFlag = True
    self.mainLoop.join()
    self.logger.debug("Основной поток завершён.")
    self.timersLoop.join()
    self.logger.debug("Поток таймеров завершён.")
    pass
  
  #Функция проверки команд.
  def ChekCommands(self, mes, vk : vkApi.VkApiMethod) -> Answer|None:
    """Обрабатывает команды, которые бот читает в чате."""
    patterns = {
      r'^\s*(https://vk\.com/[\dA-Za-zА-Яа-я_]+[\.;\s]*)+$' : self.AddCandidates,
      r'^\s*((привет)|(рот фронт)|(здравствуй)|(добрый день)|(rote? front))\s*$' : lambda mes, vk: Answer("Rote Front!"),
      r'^\s*((дай\.?)|(\$)|(ссылки\.?)|(дай ссылки\.?)|(links\.?))\s*$' : self.ReturnFromAgitations,
      r'^\s*((беру\.?)|(\.)|(взял\.?)|(\+))\s*$' : self.StartAgitations      
    }
        
    for comandTeemplate in patterns:
      if re.match(comandTeemplate, mes['text'].lower()) != None:
        return patterns[comandTeemplate](
          mes = mes, 
          vk = vk
        )
    
    return None

  #Здесь реализованы таймеры разной длительности
  def TimersLoop(self, dbPath):
    """Функция-таймер. Автоматически запускается в паралельном потоке при начале работы бота. Производит вызов функций через некоторые промежутки времени и перезапускает таймеры.
    Не запускать самостоятельно!"""

    tlDbManager = db.DataBaseManager(dbPath, logger=lg.getLogger('db')) #Создаём отдельное подключение к бд, так как эта функция будет работать в отдельном потоке
    
    ## Здесь объявляем функции которые будут вызываться таймерами.
    # Эта функция будет завершать агитации, которые агитатор не продлил или не закончил вручную.
    def ChekOldAgitations():
      
      tlDbManager.autoCommit = False
      succesAgitations = [[], [], []]
      failedAgitations = [[], [], []]
        
      inDb = tlDbManager.GetAgitations(None, '*', {db.TablesEnum.Agitations.EndDate : "< date('now')"})
      if len(inDb) > 0:
        inVk = self.session.method("messages.getConversationMembers", {"peer_id" : 2e9 + self.MAIN_CHAT_ID})
        
        #Отладка
        #print(inVk['groups'][0]['name'])
        
        
        
        #Первый прогон делаем отдельно, так как в нём мы также обновляем список текущих участников коорда (переменную party)
        i = 0
        for j in reversed(inVk['items']):
          self.party.append(j["member_id"])
          #print(j)#Отладка
          if inDb[i][2] == j["member_id"]:
            succesAgitations[0].append(inDb[i][2])
            succesAgitations[1].append(datetime.date.fromisoformat(inDb[i][0]))
            succesAgitations[2].append(inDb[i][3])
            #break Убран, так как надо пройтись по всем участникам чата
        else:
          failedAgitations[0].append(inDb[i][2])
          failedAgitations[1].append(datetime.date.fromisoformat(inDb[i][0]))
          failedAgitations[2].append(inDb[i][3])
            
        for i in range(1, len(inDb), 1):
          for j in reversed(inVk['items']):
            #print(j)#Отладка
            if inDb[i][2] == j["member_id"]:
              succesAgitations[0].append(inDb[i][2])
              succesAgitations[1].append(datetime.date.fromisoformat(inDb[i][0]))
              succesAgitations[2].append(inDb[i][3])
              break
          else:
            failedAgitations[0].append(inDb[i][2])
            failedAgitations[1].append(datetime.date.fromisoformat(inDb[i][0]))
            failedAgitations[2].append(inDb[i][3])
        
        
        
          
        tlDbManager.SuccesAgitations(
          succesAgitations[0],
          succesAgitations[1],
          succesAgitations[2],
          ["Завершено автоматически"]*len(succesAgitations[2])
          )
        tlDbManager.FailedAgitations(
          failedAgitations[0],
          failedAgitations[1],
          failedAgitations[2],
          ["Завершено автоматически"]*len(failedAgitations[2])
          ) 
              
        tlDbManager.Commit()
      self.logger.info(f"Агитации завршены автоматически. Успех: {str(len(succesAgitations[0]))}. Неудача: {str(len(failedAgitations[0]))}")
      
      
    #ChekOldAgitations() Для отладки
    
    ## Здесь объявляем функции, которые автоматически будут перевызывать таймеры, после их выполнения.
    ## Эти функции вызываются в строго определённые промежутки времени и не имеют накапливающейся погрешности, поэтому будем называть их "точными"
    def TFChekOldAgitations(timersList): # TimerFunctionChekOldAgitations | Функцию на автоматическое завершение агитаций будем вызывать каждые 24 часа. По умолчанию при запуске она будет вызываться примерно в час ночи 
      timersList[0] = threading.Timer( (23 - dt.now().hour)*3600 + (59 - dt.now().minute)*60 + (60 - dt.now().second), TFChekOldAgitations, [timersList,] ) # Повторно создаём таймер
      timersList[0].start() # Перезапускаем таймер
      self.logger.info("Запуск ежедневной проверки незаконченных агитаций.")
      ChekOldAgitations() # Вызываем основную функцию
          
    # Теперь создаём список в котором будут храниться точные таймеры, чтобы иметь возможность прервать таймеры при завершении работы бота
    timersList = []
    
    # Здесь можно выставить первый интервал ожидания таймера любым, тем самым подгадав время в которое будет вызываться функция
    timersList.append(threading.Timer( (1 + 23 - dt.now().hour)*3600 + (59 - dt.now().minute)*60 + (60 - dt.now().second), TFChekOldAgitations, [timersList,])) # Подгадываем время так, чтобы функция вызывалась примерно в час ночи
        
    for i in timersList: # Запускаем таймеры
      i.start()
      
    # Здесь будут вызываться функции, для которых не важна точность. Они будут вызываться через приблизительно равные интервалы и иметь накапливающуюся ошибку.
    # Интервалы должны быть меньше одной двух минут, так как при завершении работы бота может возникнуть задержка равная длительности интервала. 
    t = [60,] # Интервалы
    time_left = t # Буферная переменная
    fns = [lambda: 2+2,] # Функции которые будут вызываться
    # Списки должны быть одинаковой длинны, все элементы находятся во взаимном соответствии
    # Все списки должны содержать хотя бы один элемент, поэтому положил туда лямбду-пустышку 
    
    #Бесконечный цикл реализующий работу "не точных" таймеров. Завершается при безопасном заверешении работы бота.
    while not self.stopFlag:
      
      sleept = min(time_left)
      time.sleep(sleept)
      time_left = [ i-sleept for i in time_left]
      
      for i in range(len(time_left)):
        if time_left[i] == 0:
          fns[i]()
          time_left[i] = t[i]
    
    
    # Прерываем работу всех "точных" таймеров при завершении работы бота.
    for i in timersList:
      i.cancel()
    # Перед завершением работы бота запустим все важные таймерные функции (на пример проверку на завершение агитаций), 
    # вызов которых мог быть пропущен из за прерывания всех "точных таймеров"
    self.logger.debug("Завершающая проверка агитаций, ожидайте...")
    ChekOldAgitations()
    self.logger.debug("Проверка завершена.")
    pass
  
  #Здесь начинается блок функций, вызывающихся при ответе на сообщение.
  #Не нашёл способ как сделать список из лямбда-функций или чего то подобного, поэтому сами команды будем прописывать на прямую в боте.
  
  def AddCandidates(self, mes, vk : vkApi.VkApiMethod) -> Answer:
       
    #Создаём переменную в которой будет весь текст сообщения и всех его вложений
    all_text = mes['text'] + ','
    #Буферная переменная, в которую будем складывать не обработанные вложенные сообщения
    next_msgs = []
    if 'fwd_messages'in mes.keys():
      next_msgs = mes['fwd_messages']
    
    if 'reply_message' in mes.keys():
      next_msgs.append(mes['reply_message'])
    
        
    while len(next_msgs) > 0:
      all_text += next_msgs[0]['text'] + ','
      
      if 'reply_message' in next_msgs[0].keys():
        next_msgs.append(next_msgs[0]['reply_message'])
      if 'fwd_messages'in next_msgs[0].keys():
        next_msgs += next_msgs[0]['fwd_messages']
      next_msgs.pop(0)
      
    links = set(re.findall(r"https://vk\.com/[\dA-Za-zА-Яа-я_]+", all_text.lower()))
    # За один запрос получаем id как всех переданных ссылок, так и автора сообщения
    users = vk.users.get(user_ids = ",".join([link[15:] for link in links]) + ", " + str(mes['from_id']))
    who_added = users[-1]['first_name'] + ' ' + users[-1]['last_name']
    #Последний элемент массива - это информация о добавившем ссылки в чат.
    users.pop(-1)
    
    
    candidates = self.dbManager.GetCampaigningCandidates(
      fields=[db.TablesEnum.CampaigningCandidates.VkId,],
      filters = {
        db.TablesEnum.CampaigningCandidates.VkId : f"IN ({','.join([str(i['id']) for i in users])})",
        db.TablesEnum.CampaigningCandidates.CooldownDate : "> date('now')"
      }
    )
    fwd_msgs = []
    result_message_text = ""
    ids = [i[0] for i in candidates]
    if len(ids) > 0:
      
            
      # Перебираем 
      for i in range(0, len(users), 1): 
        if len(ids) == 0:
          break
        if users[i]['id'] in ids or users[i]['id'] in self.party:
          result_message_text = result_message_text + f"{links[i]}\n"
          ids.remove(users[i]['id'])
          users.remove(i)
          
      if mes['peer_id'] > 2e9:    #Если сообщение пришло из беседы
        #После того, как перебрали ссылки, не подходящие для агитации, пытаемся удалить сообщение человека, передавшего эти ссылки    
        try: 
          vk.messages.delete(   
            peer_id = mes['peer_id']-2e9,
            cmids = mes['conversation_message_id'],
            delete_for_all = 1
          )
          # Если возникнет исключение, этот кусок (до exception) не выполнится
          if len(users) > 0:
            result_message_text = "@id" + str(mes['from_id']) + """, из отправленных вами ссылок, для агитации подходят только следующие:
            """ + '\n'.join(["https://vk.com/id" + i['id'] for i in users])          
          else:
            result_message_text = "@id" + str(mes['from_id']) + ", переданные вами ссылки не подходят для агитации."
        except vkApi.ApiError as er:
          if er.code == 15: # Если не получается удалить сообщение, потому что его автор администратор, то уведомляем его о том, что часть его ссылок не подходят
            result_message_text = "@id" + str(mes['from_id']) + ", эти ссылки не доступны для агитации в данный момент:\n" + result_message_text # Текст
            fwd_msgs  = ['conversation_message_id']+328 # Id сообщения в котором есть неподходящие ссылки. Его мы указываем, чтобы прикрпеить к ответу
          else:
            self.logger.error(er)
        except Exception as ex:
          self.logger.exception(ex)
      else:
        result_message_text = "Эти ссылки не доступны для агитации в данный момент:\n" + result_message_text # Текст
        fwd_msgs  = ['conversation_message_id']+328 # Id сообщения в котором есть неподходящие ссылки. Его мы указываем, чтобы прикрпеить к ответу
      
        
      
    
    in_blackList = self.dbManager.AddCampaigningCandidates(
      vk_id= [str(i['id']) for i in users],
      full_name= [i['first_name'] + ' ' + i['last_name'] for i in users],
      who_added= [who_added]*len(users)
      )
    
    if len(in_blackList) > 0:
      result_message_text += "\n Эти ссылки находятся в чёрном списке:\n" + '\n'.join(["https://vk.com/id" + i['id'] for i in in_blackList])
    
    if len(result_message_text) > 1:
      return Answer(result_message_text, fwd_msgs)
    else:
      return None
    
  def ReturnFromAgitations(self, mes, vk : vkApi.VkApiMethod) -> Answer:
    num = re.search(r'\d{1,2}', mes['text'].lower())
    if num != None:
      num = int(num)
    else:
      num = int(10)
    
        
    ids = self.dbManager.GetCampaigningCandidates(
      count=num,
      fields=[db.TablesEnum.CampaigningCandidates.VkId],
      filters={db.TablesEnum.CampaigningCandidates.CooldownDate : "< date('now')"}
      )
    
    if len(ids) > 0:
      return Answer("\n".join(['https://vk.com/id'+str(i[0]) for i in ids]))
    else:
      return None
    
  
  
  
    # https://vk.com/megagiperden
    # https://vk.com/communarchik
    # https://vk.com/cadka1905
    # https://vk.com/id675953664
    # https://vk.com/korol_metall
    # https://vk.com/ckckckckkskkksfk
    
  def StartAgitations(self, mes, vk : vkApi.VkApiMethod) -> Answer:
    
    #Создаём переменную в которой будет весть текст сообщения и всех его вложений
    all_text = mes['text'] + ','
    #Буферная переменная, в которую будем складывать не обработанные вложенные сообщения
    next_msgs = []
    if 'fwd_messages'in mes.keys():
      next_msgs = mes['fwd_messages']
    
    if 'reply_message' in mes.keys():
      next_msgs.append(mes['reply_message'])
    
        
    while len(next_msgs) > 0:
      all_text += next_msgs[0]['text'] + ','
      
      if 'reply_message' in next_msgs[0].keys():
        next_msgs.append(next_msgs[0]['reply_message'])
      if 'fwd_messages'in next_msgs[0].keys():
        next_msgs += next_msgs[0]['fwd_messages']
      next_msgs.pop(0)
      
    
    links = set(re.findall(r"https://vk\.com/[\dA-Za-zА-Яа-я_]+", all_text.lower()))
    users = vk.users.get(user_ids = ",".join([link[15:] for link in links]) + ", " + str(mes['from_id']))
    agitator = users[-1]['first_name'] + ' ' + users[-1]['last_name']
    users.pop(-1)
    
    #Патаемся запустить агитации. id тех людей, агитация которых сейчас не возможна возвращаем в breake_ids
    breake_ids = self.dbManager.StartAgitations(vk_id= [str(i['id']) for i in users], agitators= [agitator]*len(users))
    
    # В целях отладки будем отправлять сообщения о том, что человек начал агитацию ему в личку.
    # В будущющем эту функцию уберём
    
    rplmsg = '\n'.join( [ 'https://vk.com/id' + str(i['id']) for i in users if str(i['id']) not in breake_ids ])    
    
    if len(rplmsg) > 0: 
      try:        
        vk.messages.send( #Отправляем сообщение
                    user_id=mes['from_id'],
                    random_id = int(time.time()*1e6),
                    message = "Агитация начата для:\n" +  rplmsg
        )  
      except vkApi.ApiError as er:
        self.logger.debug(er)
    
    if len(breake_ids) > 0:
      return Answer("Данные кандидаты не доступны для агитации:\n" + '\n'.join(['https://vk.com/id'+id for id in breake_ids]))
    else:
      return None