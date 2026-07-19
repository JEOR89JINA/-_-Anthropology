import os
import telebot
from groq import Groq
import requests
import re

# 1. جلب المفاتيح من إعدادات ريلواي ومعرف مجموعتك
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROUP_CHAT_ID = -1004482110218
UNSPLASH_ACCESS_KEY = "kIjWpGPgkjcSmYhgFRVA-guVHTwXtVmm-Ihfarl_Hn0"

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("خطأ: لم يتم العثور على TELEGRAM_TOKEN أو GROQ_API_KEY في متغيرات ريلواي!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# دالة مطورة ومصلحة بالكامل لجلب كلمات بحث دقيقة وصورة مطابقة من Unsplash
def get_unsplash_photo(query_text):
    try:
        # نطلب من جروج إعطاء كلمة رئيسية واحدة أو اثنتين صافية تماماً بالإنجليزية
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a keyword extractor. Extract 1 or 2 specific English keywords from the text for image search. Output ONLY the keywords. No explanation, no intro, no quotes, no punctuation. Example user text: 'حضارة الاسكيمو', your output: 'Inuit culture'."},
                {"role": "user", "content": query_text}
            ],
            temperature=0.1,
        )
        # الحل النهائي هنا لقراءة رد جروج بشكل صحيح ومحدث دون أخطاء القوائم
        raw_query = completion.choices[0].message.content.strip()
        search_query = re.sub(r'[^a-zA-Z0-9\s]', '', raw_query).strip()
        
        if not search_query:
            search_query = "anthropology"
    except:
        search_query = "anthropology"

    # البحث الدقيق في Unsplash
    url = f"https://unsplash.com{search_query}&client_id={UNSPLASH_ACCESS_KEY}"
    try:
        response = requests.get(url, timeout=7)
        if response.status_code == 200:
            return response.json()['urls']['regular']
    except:
        pass
    return "https://unsplash.com"

# دالة ذكاء جروج (Groq) للرد الأنثروبولوجي المصلحة أيضاً
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
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
        )
        # قراءة الرد بالطريقة البرمجية الصحيحة والمحدثة والمستقرة
        return completion.choices[0].message.content
    except Exception as e:
        return f"عذراً، واجهت مشكلة في الاتصال بعقلي الأنثروبولوجي الرقمي! الخطأ: {e}"

# أولاً: استقبال أوامر الترحيب والمساعدة
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "🔬 مرحباً بك! أنا مستشارك البروفيسور الذكي في علم الأنثروبولوجيا. أستطيع تحليل منشورات القناة وصنع توضيح بالصور الدقيقة هنا أو في المجموعة."
    bot.reply_to(message, welcome_text)

# ثانياً: استقبال رسائل المحادثات الخاصة
@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_private_messages(message):
    if message.text and not message.text.startswith('/'):
        reply = get_groq_response(message.text, context_type="comment")
        if len(reply) > 4000:
            reply = reply[:4000] + "\n\n...(تم اختصار النص لقيود تليجرام)"
        bot.reply_to(message, reply)

# ثالثاً: مراقبة وتحديث التفاعل داخل المجموعة والتعليقات مع الصور الدقيقة
@bot.message_handler(func=lambda message: str(message.chat.id) == str(GROUP_CHAT_ID))
def handle_group_messages(message):
    bot_username = bot.get_me().username
    
    # 1. رصد المنشورات التلقائية القادمة من القناة للمجموعة
    is_channel_forward = message.forward_from_chat and message.forward_from_chat.type == "channel"
    is_auto_forward = hasattr(message, 'is_automatic_forward') and message.is_automatic_forward
    
    if is_channel_forward or is_auto_forward:
        post_text = message.text if message.text else message.caption
        if post_text:
            analysis = get_groq_response(post_text, context_type="channel_post")
            photo_url = get_unsplash_photo(post_text)
            
            caption_text = f"🔬 **تحليل أنثروبولوجي للمنشور الجديد:**\n\n{analysis}"
            if len(caption_text) > 1000:
                caption_text = caption_text[:1000] + "\n\n...(تم اختصار النص لقيود تليجرام)"
                
            try:
                bot.send_photo(GROUP_CHAT_ID, photo=photo_url, caption=caption_text, parse_mode="Markdown", reply_to_message_id=message.message_id)
            except:
                bot.reply_to(message, caption_text, parse_mode="Markdown")
        return

    # 2. رصد تعليقات الأعضاء وردودهم داخل المجموعة
    if message.text:
        is_comment = message.reply_to_message is not None
        is_mentioned = f"@{bot_username}" in message.text
        contains_keyword = "أنثروبولوج" in message.text

        if is_comment or is_mentioned or contains_keyword:
            clean_text = message.text.replace(f"@{bot_username}", "").strip()
            groq_reply = get_groq_response(clean_text, context_type="comment")
            
            if len(groq_reply) > 4000:
                groq_reply = groq_reply[:4000] + "\n\n...(تم الاختصار)"
                
            bot.reply_to(message, groq_reply)

print("البوت الأنثروبولوجي المطور بالكامل بالصور الذكية يعمل الآن...")
bot.infinity_polling()
        
