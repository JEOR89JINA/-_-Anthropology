import os
import telebot
from groq import Groq

# 1. إعداد البيانات (تم دمج مفتاح جروج ومعرف المجموعة مباشرة)
# توكن تليجرام سيتم قراءته بأمان من إعدادات Railway (Variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = "GROQ_API_KEY"
GROUP_CHAT_ID = -1004482110218

# التحقق من وجود توكن تليجرام قبل التشغيل
if not TELEGRAM_TOKEN:
    raise ValueError("خطأ: لم يتم العثور على TELEGRAM_TOKEN في إعدادات البيئة (Variables)!")

# تهيئة البوت ومنصة Groq
bot = telebot.TeleBot(TELEGRAM_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# دالة لإرسال النص إلى ذكاء جروج (Groq) والحصول على رد أنثروبولوجي فوري وسريع
def get_groq_response(prompt, context_type="comment"):
    
    # توجيه الـ AI ليتصرف كخبير أنثروبولوجيا متميز
    system_instruction = (
        "أنت بروفيسور وخبير متميز وذكي جداً في علم الأنثروبولوجيا (علم الإنسان الثقافي والحيوي والاجتماعي). "
        "ردودك يجب أن تكون عميقة، علمية، ومبسطة في نفس الوقت، وتطرح تحليلات أنثروبولوجية ممتعة بناءً على النص المعطى."
    )
    
    if context_type == "channel_post":
        user_message = f"اكتب توضيحاً وتحليلاً أنثروبولوجياً عميقاً ومثيراً للاهتمام حول هذا المنشور: {prompt}"
    else:
        user_message = f"رد بشكل أنثروبولوجي وذكي على هذا التعليق أو السؤال: {prompt}"

    try:
        # استخدام نموذج Llama 3 المتوفر في Groq والسريع جداً
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
        )
        return completion.choices.message.content
    except Exception as e:
        return f"عذراً، واجهت مشكلة في الاتصال بعقلي الأنثروبولوجي عبر منصة Groq! الخطأ: {e}"

# أولاً: مراقبة منشورات القناة والرد عليها في المجموعة
@bot.channel_post_handler(func=lambda message: True)
def handle_channel_post(message):
    post_text = message.text if message.text else message.caption
    if post_text:
        # إرسال المنشور إلى جروج لتحليله
        analysis = get_groq_response(post_text, context_type="channel_post")
        # إرسال التحليل الأنثروبولوجي فوراً إلى المجموعة التابعة للقناة
        bot.send_message(GROUP_CHAT_ID, f"🔬 **تحليل أنثروبولوجي للمنشور الجديد:**\n\n{analysis}", parse_mode="Markdown")

# ثانياً: الرد على تعليقات وأسئلة المشتركين في المجموعة
@bot.message_handler(func=lambda message: str(message.chat.id) == str(GROUP_CHAT_ID))
def handle_group_comments(message):
    bot_username = bot.get_me().username
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
    is_mentioned = message.text and f"@{bot_username}" in message.text
    contains_keyword = message.text and "أنثروبولوج" in message.text

    if is_reply_to_bot or is_mentioned or contains_keyword:
        clean_text = message.text.replace(f"@{bot_username}", "").strip()
        # جلب الرد من جروج
        groq_reply = get_groq_response(clean_text, context_type="comment")
        # الرد على المشترك مباشرة
        bot.reply_to(message, groq_reply)

# تشغيل البوت بشكل مستمر
print("البوت الأنثروبولوجي الذكي (Groq) يعمل الآن بنجاح على السيرفر...")
bot.infinity_polling()
        
