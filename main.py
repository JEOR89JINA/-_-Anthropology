import os
import telebot
from groq import Groq

# 1. إعداد البيانات بأمان من بيئة عمل ريلواي ومعرف مجموعتك
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROUP_CHAT_ID = -1004482110218

# التحقق من وجود المفاتيح في ريلواي قبل تشغيل البوت
if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("خطأ: لم يتم العثور على TELEGRAM_TOKEN أو GROQ_API_KEY في متغيرات ريلواي!")

# تهيئة البوت ومنصة Groq
bot = telebot.TeleBot(TELEGRAM_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# دالة لجلب رد أنثروبولوجي ذكي وسريع من Groq (Llama 3)
def get_groq_response(prompt, context_type="comment"):
    system_instruction = (
        "أنت بروفيسور وخبير متميز وذكي جداً في علم الأنثروبولوجيا (علم الإنسان الثقافي والحيوي والاجتماعي). "
        "ردودك يجب أن تكون عميقة، علمية، ومبسطة في نفس الوقت، وتطرح تحليلات أنثروبولوجية ممتعة بناءً على النص المعطى."
    )
    
    if context_type == "channel_post":
        user_message = f"اكتب توضيحاً وتحليلاً أنثروبولوجياً عميقاً ومثيراً للاهتمام حول هذا المنشور: {prompt}"
    else:
        user_message = f"رد بشكل أنثروبولوجي وذكي وبإيجاز علمي على هذا التعليق أو السؤال: {prompt}"

    try:
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

# التحديث الجديد: مراقبة الرسائل القادمة للمجموعة والتعامل مع التعليقات
@bot.message_handler(func=lambda message: str(message.chat.id) == str(GROUP_CHAT_ID))
def handle_group_messages(message):
    bot_username = bot.get_me().username
    
    # أولاً: التحقق مما إذا كانت الرسالة هي منشور تم توجيهه تلقائياً من القناة إلى المجموعة (بداية صندوق التعليقات)
    is_channel_post_forwarded = message.forward_from_chat and message.forward_from_chat.type == "channel"
    is_auto_forward = hasattr(message, 'is_automatic_forward') and message.is_automatic_forward
    
    if is_channel_post_forwarded or is_auto_forward:
        post_text = message.text if message.text else message.caption
        if post_text:
            # طلب التحليل من جروج
            analysis = get_groq_response(post_text, context_type="channel_post")
            # الرد مباشرة "كـ تعليق أول" على المنشور الموجه في المجموعة
            bot.reply_to(message, f"🔬 **تحليل أنثروبولوجي للمنشور الجديد:**\n\n{analysis}", parse_mode="Markdown")
        return

    # ثانياً: مراقبة تعليقات المشتركين داخل صندوق التعليقات أو الردود العادية
    # تليجرام يعتبر التعليق تحت المنشور بمثابة Reply للرسالة الأصلية الموجهة من القناة
    is_comment = message.reply_to_message and message.reply_to_message.forward_from_chat and message.reply_to_message.forward_from_chat.type == "channel"
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
    is_mentioned = message.text and f"@{bot_username}" in message.text
    contains_keyword = message.text and "أنثروبولوج" in message.text

    # إذا كان تعليقاً على منشور القناة، أو رداً على البوت، أو منشن، أو ذكر العلم
    if is_comment or is_reply_to_bot or is_mentioned or contains_keyword:
        if message.text:
            clean_text = message.text.replace(f"@{bot_username}", "").strip()
            # جلب الرد من جروج
            groq_reply = get_groq_response(clean_text, context_type="comment")
            # الرد على تعليق المشترك مباشرة داخل صندوق التعليقات
            bot.reply_to(message, groq_reply)

# تشغيل البوت
print("البوت المطور للتعليقات والمنشورات يعمل بنجاح...")
bot.infinity_polling()
