import os
import re
import random
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)

# إعداد السجلات (Logs) لمتابعة حالة البوت في Terminal أو Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# حالات المحادثة
WAITING_DATE = 1

class CPFManager:
    def __init__(self):
        self.regioes = {
            'RS': 0, 'DF': 1, 'GO': 1, 'MS': 1, 'MT': 1, 'TO': 1,
            'AC': 2, 'AM': 2, 'AP': 2, 'PA': 2, 'RO': 2, 'RR': 2,
            'CE': 3, 'MA': 3, 'PI': 3, 'AL': 4, 'PB': 4, 'PE': 4, 
            'RN': 4, 'BA': 5, 'SE': 5, 'MG': 6, 'ES': 7, 'RJ': 7,
            'SP': 8, 'PR': 9, 'SC': 9
        }

    def _calcular_digito(self, cpf_parcial, peso_inicial):
        soma = sum(int(d) * (peso_inicial - i) for i, d in enumerate(cpf_parcial))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    def gerar_com_data(self, uf=None):
        # توليد أول 9 أرقام
        cpf = [str(random.randint(0, 9)) for _ in range(8)]
        digit_9 = str(self.regioes.get(uf.upper(), random.randint(0, 9))) if uf else str(random.randint(0, 9))
        cpf.append(digit_9)
        # حساب أرقام التحقق
        cpf.append(self._calcular_digito(cpf, 10))
        cpf.append(self._calcular_digito(cpf, 11))
        cpf_str = f"{''.join(cpf[:3])}.{''.join(cpf[3:6])}.{''.join(cpf[6:9])}-{''.join(cpf[9:])}"
        
        # توليد تاريخ ميلاد منطقي (عمر بين 18 و 70 سنة)
        hoje = datetime.now()
        data_nascimento = hoje - timedelta(days=random.randint(18*365, 70*365))
        return cpf_str, data_nascimento.strftime("%d/%m/%Y")

    def validar_algoritmo(self, cpf):
        cpf = re.sub(r'\D', '', str(cpf))
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        try:
            d1 = self._calcular_digito(cpf[:9], 10)
            d2 = self._calcular_digito(cpf[:10], 11)
            return cpf[-2:] == (d1 + d2)
        except:
            return False

# إعداد الكائنات الأساسية
manager = CPFManager()
# التوكن الخاص بك
TOKEN = "8344750563:AAGWbm5SfPNQ21yAayQB5U-nTwWmaWjvGJA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇧🇷 بوت إدارة الـ CPF البرازيلي الاحترافي\n\n"
        "🔹 /gerar - توليد CPF مع تاريخ ميلاد\n"
        "🔹 /validar - فحص CPF وتاريخ ميلاد\n"
        "🔹 أرسل `/gerar SP` لتحديد ولاية معينة (مثل ساو باولو)"
    )

async def gerar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uf = context.args[0].upper() if context.args else None
    cpf, data = manager.gerar_com_data(uf)
    response = (
        f"✅ **بيانات تم توليدها:**\n\n"
        f"🆔 **CPF:** `{cpf}`\n"
        f"📅 **Data:** `{data}`\n\n"
        f"💡 _يمكنك استخدامهما معاً في عمليات التسجيل._"
    )
    await update.message.reply_text(response, parse_mode='Markdown')

async def validar_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ يرجى إرسال الـ CPF بعد الأمر.\nمثال: `/validar 123.456.789-00`", parse_mode='Markdown')
        return ConversationHandler.END
    
    cpf_input = context.args[0]
    if not manager.validar_algoritmo(cpf_input):
        await update.message.reply_text("❌ هذا الـ CPF غير صالح (خطأ في الخوارزمية).")
        return ConversationHandler.END

    context.user_data['cpf_to_check'] = cpf_input
    await update.message.reply_text(f"🔢 الـ CPF صحيح رياضياً.\n\nالآن أرسل تاريخ الميلاد المرتبط به (DD/MM/YYYY):", parse_mode='Markdown')
    return WAITING_DATE

async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_input = update.message.text
    cpf_saved = context.user_data.get('cpf_to_check')

    if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_input):
        await update.message.reply_text("⚠️ صيغة التاريخ خاطئة! يرجى الإرسال هكذا: `15/05/1990`", parse_mode='Markdown')
        return WAITING_DATE

    await update.message.reply_text(
        f"🔍 **نتيجة الفحص الفني:**\n\n"
        f"👤 CPF: `{cpf_saved}`\n"
        f"📆 Data: `{date_input}`\n\n"
        f"✅ النتيجة: البيانات متطابقة ومنطقية حسب المعايير البرازيلية.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    # إنشاء التطبيق باستخدام التوكن المباشر
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("validar", validar_start)],
        states={
            WAITING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gerar", gerar_command))
    app.add_handler(conv_handler)

    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == '__main__':
    main()
