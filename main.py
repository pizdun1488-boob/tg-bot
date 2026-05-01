import logging
import os
TOKEN = os.getenv("BOT_TOKEN")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== НАСТРОЙКИ ====================
# Вставьте токен от @BotFather
BOT_USERNAME = '@eto_obman_bot'

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== БАЗА ДАННЫХ СЦЕНАРИЕВ (АДАПТИРОВАНО ПОД РБ) ====================
SCENARIOS = {
    'bank_call': {
        'title': '🏦 Звонок из "службы безопасности банка"',
        'description': 'Вам звонит "сотрудник Беларусбанка/БПС-Сбербанк/Альфа-Банка" и сообщает о подозрительной операции по карте. Говорит, что деньги пытаются украсть, и нужно срочно перевести их на "безопасный счёт".',
        'steps': [
            {
                'question': 'Как вы поступите?',
                'options': [
                    {'text': 'Назову данные карты и код из СМС', 'is_correct': False, 
                     'explanation': '❌ Ошибка! Настоящий сотрудник банка НИКОГДА не спрашивает данные карты или коды. Это мошенники!\n\n📚 Ст. 209 УК РБ (Мошенничество). Наказывается штрафом, исправительными работами или лишением свободы до 3 лет.'},
                    {'text': 'Перезвоню в банк по номеру на карте', 'is_correct': True, 
                     'explanation': '✅ Правильно! Положите трубку и перезвоните по официальному номеру (например, Беларусбанк: 147).\n\n📚 Ст. 212 УК РБ (Хищение путём использования компьютерной техники) — мошенники часто пытаются получить удалённый доступ.'},
                    {'text': 'Установлю приложение по ссылке от "сотрудника"', 'is_correct': False, 
                     'explanation': '❌ Ошибка! Это программа удалённого доступа. Мошенники получат полный контроль над телефоном.\n\n📚 Ст. 349 УК РБ (Несанкционированный доступ к компьютерной информации).'},
                ]
            },
            {
                'question': 'Вам пришло СМС с кодом и просят продиктовать его для "отмены операции". Ваши действия?',
                'options': [
                    {'text': 'Продиктую код, чтобы спасти деньги', 'is_correct': False, 
                     'explanation': '❌ Ошибка! Код из СМС — это ключ к вашему счету. Никому его не сообщайте.\n\n📚 Ст. 209 УК РБ. Мошенники используют методы социальной инженерии.'},
                    {'text': 'Не буду ничего диктовать и позвоню на горячую линию банка', 'is_correct': True, 
                     'explanation': '✅ Верно! Телефоны горячих линий: Беларусбанк – 147, Приорбанк – 154, БПС-Сбербанк – 133. Звоните только по этим номерам.'},
                ]
            }
        ]
    },
    'friend_in_trouble': {
        'title': '👥 Просьба о помощи от "друга" (Viber/Telegram)',
        'description': 'В мессенджер приходит сообщение от друга: "Привет! Выручай, срочно нужно 150 рублей на карту. Потом объясню. Очень срочно!"',
        'steps': [
            {
                'question': 'Ваша реакция?',
                'options': [
                    {'text': 'Сразу переведу — друг не обманет', 'is_correct': False, 
                     'explanation': '❌ Ошибка! Аккаунт могли взломать. Деньги уйдут мошенникам.\n\n📚 Ст. 209 УК РБ. Потерпевшими часто становятся из-за доверчивости.'},
                    {'text': 'Позвоню другу по обычному телефону', 'is_correct': True, 
                     'explanation': '✅ Отлично! Только личный звонок или встреча подтвердит, что друг действительно нуждается.\n\n📚 Если друг подтвердил — можно оформить перевод, но лучше составить расписку (ст. 162 ГК РБ).'},
                    {'text': 'Задам вопрос, ответ на который знает только друг', 'is_correct': True, 
                     'explanation': '✅ Хороший способ! Контрольный вопрос поможет выявить мошенника (например, спросите, где вы вместе отдыхали).'},
                ]
            }
        ]
    },
    'government_services': {
        'title': '🏛️ "Проблемы с паспортом или налогами"',
        'description': 'Приходит СМС: "Ваш паспорт заблокирован/обнаружена задолженность. Для уточнения перейдите по ссылке: точно_не_мошенники.com"',
        'steps': [
            {
                'question': 'Как поступите?',
                'options': [
                    {'text': 'Перейду по ссылке и введу данные', 'is_correct': False, 
                     'explanation': '❌ Опасно! Это фишинговый сайт. Ваши паспортные данные украдут.\n\n📚 Ст. 212 УК РБ (Хищение путём модификации компьютерной информации).'},
                    {'text': 'Удалю сообщение и зайду на официальный портал', 'is_correct': True, 
                     'explanation': '✅ Правильно! Все официальные сервисы: portal.gov.by, Министерство по налогам и сборам (nalog.gov.by), ЕРИП. Никогда не переходите по ссылкам из СМС.'},
                    {'text': 'Перезвоню по номеру из СМС', 'is_correct': False, 
                     'explanation': '❌ Ошибка! Номер принадлежит мошенникам. Настоящие госорганы не присылают ссылки в СМС.'},
                ]
            }
        ]
    },
    'inheritance': {
        'title': '💰 "Вам положен выигрыш/компенсация"',
        'description': 'Вам звонят и сообщают, что вы выиграли в лотерею или вам положена компенсация от государства. Для получения нужно оплатить "налог" или "пошлину" через ЕРИП.',
        'steps': [
            {
                'question': 'Ваши действия?',
                'options': [
                    {'text': 'Переведу небольшую сумму через ЕРИП, чтобы получить крупный выигрыш', 'is_correct': False, 
                     'explanation': '❌ Ошибка! ЕРИП — это система оплаты, но мошенники тоже используют её, чтобы получить ваши деньги. Никакого выигрыша не будет.\n\n📚 Ст. 209 УК РБ.'},
                    {'text': 'Попрошу прислать официальное уведомление по почте', 'is_correct': True, 
                     'explanation': '✅ Верно! Все официальные уведомления приходят только по почте или через нотариуса. Настоящие лотереи и наследства не требуют предоплат.'},
                ]
            }
        ]
    }
}

# ==================== ПАМЯТКА ДЛЯ ЖЕРТВ МОШЕННИКОВ (ПО ЗАКОНОДАТЕЛЬСТВУ РБ) ====================
VICTIM_GUIDE = """
📌 **Если вы стали жертвой мошенников (действия в РБ):**

1️⃣ **Немедленно заблокируйте карту** через мобильное приложение или позвоните в банк (номера: Беларусбанк – 147, БПС-Сбербанк – 148, Альфа-Банк – 198).

2️⃣ **Позвоните в милицию** по номеру **102** или обратитесь в ближайшее РОВД. Возьмите с собой паспорт.

3️⃣ **Сохраните все доказательства:**
   - Скриншоты переписки
   - Номера телефонов мошенников
   - Дату и время звонков
   - Номера счетов, куда перевели деньги

4️⃣ **Напишите заявление** в милицию. В заявлении укажите все обстоятельства. Вам выдадут талон-уведомление.

5️⃣ **Обратитесь в банк с заявлением** о несанкционированной операции (если успели перевести деньги). Банк может приостановить транзакцию.

📚 **Статьи УК РБ**, которые чаще всего нарушают мошенники:
- **Ст. 209** – Мошенничество (завладение имуществом путём обмана)
- **Ст. 212** – Хищение путём использования компьютерной техники
- **Ст. 349** – Несанкционированный доступ к компьютерной информации
- **Ст. 351** – Разработка и распространение вредоносных программ

🛡️ **Полезные контакты:**
- Сайт Министерства внутренних дел: mvd.gov.by (раздел "Противодействие киберпреступности")
"""

# ==================== КЛАВИАТУРЫ ====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📚 Начать обучение", callback_data='start_learning')],
        [InlineKeyboardButton("ℹ️ О проекте", callback_data='about')],
        [InlineKeyboardButton("🚨 Памятка жертве", callback_data='victim_guide')],
        [InlineKeyboardButton("📞 Контакты (милиция/банки)", callback_data='contacts')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_scenarios_keyboard():
    keyboard = []
    for sc_id, sc_data in SCENARIOS.items():
        keyboard.append([InlineKeyboardButton(sc_data['title'], callback_data=f'scenario_{sc_id}')])
    keyboard.append([InlineKeyboardButton("🔙 В главное меню", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение при команде /start"""
    user = update.effective_user
    welcome_text = f"""
👋 Привет, {user.first_name}!

Добро пожаловать в **«Это обман?»** — интерактивный тренажёр по кибербезопасности для жителей Беларуси.

🔐 Здесь вы научитесь распознавать мошенников в игровой форме. Вас ждут реальные сценарии: звонки из "банка", сообщения от "друзей" в Viber, фальшивые СМС от неизвестных сайтов.

✅ Выбирайте варианты ответов и узнавайте, как правильно поступать. Если ошибётесь — бот покажет, какая статья Уголовного кодекса РБ нарушается и как действовать.

👉 Нажмите **«Начать обучение»**, чтобы приступить!
    """
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'main_menu':
        await query.edit_message_text(
            "🔍 Главное меню. Выберите действие:",
            reply_markup=get_main_keyboard()
        )

    elif data == 'start_learning':
        await query.edit_message_text(
            "📚 Выберите сценарий для тренировки:",
            reply_markup=get_scenarios_keyboard()
        )

    elif data == 'about':
        about_text = """
ℹ️ **О проекте «Это обман?»**

Этот бот создан для повышения цифровой грамотности граждан Республики Беларусь. Мы используем геймификацию, чтобы в безопасной среде обучить вас распознавать основные виды мошенничества.

**Как это работает:**
1. Вы выбираете сценарий (звонок из банка, сообщение от "друга" и т.д.)
2. Бот задаёт вопросы, вы выбираете вариант ответа
3. Если ответ правильный — получаете похвалу и объяснение
4. Если ошибаетесь — бот подробно разбирает ошибку и ссылается на статьи Уголовного кодекса РБ

**Правовая основа:** Все сценарии основаны на реальных случаях, зарегистрированных в МВД РБ. Ссылки на статьи УК РБ актуальны на 2025 год.

Разработчик: Открытый проект по кибербезопасности
        """
        await query.edit_message_text(about_text, reply_markup=get_main_keyboard())

    elif data == 'victim_guide':
        await query.edit_message_text(
            VICTIM_GUIDE,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

    elif data == 'contacts':
        contacts_text = """
📞 **Полезные контакты (Республика Беларусь):**

🚔 **Милиция:** 102 (круглосуточно)

🏦 **Горячие линии банков:**
• Беларусбанк – 147
• БПС-Сбербанк – 148
• Альфа-Банк – 198
• Белагропромбанк – 136

💻 **Сайт МВД (кибербезопасность):** mvd.gov.by
• Раздел «Противодействие киберпреступности»
• Памятки и рекомендации

📱 **Мобильные приложения:**
• Официальные приложения банков (скачивайте только из официальных магазинов!)
        """
        await query.edit_message_text(contacts_text, reply_markup=get_main_keyboard())

    elif data.startswith('scenario_'):
        sc_id = data.replace('scenario_', '')
        context.user_data['current_scenario'] = sc_id
        context.user_data['step_index'] = 0
        
        scenario = SCENARIOS[sc_id]
        step = scenario['steps'][0]
        
        # Формируем клавиатуру с вариантами ответов
        keyboard = []
        for i, opt in enumerate(step['options']):
            callback = f'answer_{i}_' + ('correct' if opt['is_correct'] else 'wrong')
            keyboard.append([InlineKeyboardButton(opt['text'], callback_data=callback)])
        
        await query.edit_message_text(
            f"*{scenario['title']}*\n\n_{scenario['description']}_\n\n**Вопрос 1:** {step['question']}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith('answer_'):
        parts = data.split('_')
        opt_index = int(parts[1])
        result = parts[2]  # 'correct' или 'wrong'
        
        sc_id = context.user_data.get('current_scenario')
        step_index = context.user_data.get('step_index', 0)
        
        if sc_id and sc_id in SCENARIOS:
            scenario = SCENARIOS[sc_id]
            step = scenario['steps'][step_index]
            selected_opt = step['options'][opt_index]
            
            # Показываем объяснение
            explanation = selected_opt['explanation']
            
            # Проверяем, есть ли следующий шаг
            if step_index + 1 < len(scenario['steps']):
                # Переходим к следующему вопросу
                keyboard = [[InlineKeyboardButton("➡️ Следующий вопрос", callback_data='next_question')]]
                await query.edit_message_text(
                    f"**Результат:**\n\n{explanation}\n\n---\n\n✅ Переходим к следующему вопросу...",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # Сценарий завершён
                keyboard = [
                    [InlineKeyboardButton("📚 Другие сценарии", callback_data='start_learning')],
                    [InlineKeyboardButton("🔙 В главное меню", callback_data='main_menu')]
                ]
                await query.edit_message_text(
                    f"**Результат:**\n\n{explanation}\n\n---\n\n🎉 **Сценарий пройден!**\n\nВы успешно завершили обучение по этому сценарию. Хотите попробовать другой?",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await query.edit_message_text("Ошибка. Попробуйте начать заново.", reply_markup=get_main_keyboard())

    elif data == 'next_question':
        sc_id = context.user_data.get('current_scenario')
        step_index = context.user_data.get('step_index', 0) + 1
        context.user_data['step_index'] = step_index
        
        if sc_id and sc_id in SCENARIOS:
            scenario = SCENARIOS[sc_id]
            if step_index < len(scenario['steps']):
                step = scenario['steps'][step_index]
                
                # Формируем клавиатуру
                keyboard = []
                for i, opt in enumerate(step['options']):
                    callback = f'answer_{i}_' + ('correct' if opt['is_correct'] else 'wrong')
                    keyboard.append([InlineKeyboardButton(opt['text'], callback_data=callback)])
                
                await query.edit_message_text(
                    f"*{scenario['title']}*\n\n**Вопрос {step_index + 1}:** {step['question']}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

# ==================== ЗАПУСК БОТА ====================
def main():
    """Запуск бота"""
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
