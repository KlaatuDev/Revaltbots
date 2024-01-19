import BotMain
import RASqliteDataBaseManager as db
from datetime import date as dt

import sqlite3





# Функция StartAgitations выдаёт ошибку при попытке выставить cooldown_date
# Проверь
#Исправил 2024-01-01

# При неправильно переданной дате начала агитации, 
# функция SuccessAgitations, при выставленном параметре cascade в True, может стереть человека из кандидатов на агитацию и удалить все неудачные агитации с ним,
# но не закончит агитацию с ним успехом (т.к. не найдёт этого человека по дате)
# Возможно это является проблемой, но скорее всего такие утечки будет закрывать бот при ежедневной проверке незаконченных агитаций.

# print(f"{dt(2024, 5, 10)}")
# con = sqlite3.connect('Bot.db')
# con.execute(f"DELETE FROM {db.TablesEnum.CampaigningCandidates.value}")
# # con.execute(f"""UPDATE campaigning_candidates
# #                 SET cooldown_date = '{dt(2024, 5, 10)}'
# #                 WHERE vk_id = 1;""")
# con.commit()

# dbmng = db.DataBaseManager()
# print(dbmng.GetCurrentAgitations())
# dbmng.SuccesAgitations(
#     [1,2,3],
#     [dt(2024, 1, 1)]*3,
#     ['paoan']*3,
#     ['Auto']*3,
#     [dt.today()]*3,
#     [dt(2024, 6, 10), dt(2024, 11, 22), dt(2024, 1, 8)]    
# )



bot = BotMain.AgitBot()

bot.Start()
#bot.MainLoop('Bot.db')
#bot.timerLoop.start()
#bot.TimersLoop()


while input() != "End":
    print('Not_End')
    
bot.End()