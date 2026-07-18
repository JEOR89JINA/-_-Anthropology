import logging
import os
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")
CHANNEL_ID         = os.environ.get("CHANNEL_ID", "")
DISCUSSION_GROUP_ID = -1004482110218

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT = """أنت خبير في علم الأنثروبولوجيا (علم الإنسان). مهمتك هي:
1. تحليل منشورات القناة الأنثروبولوجية وإضافة تعليقات علمية ثرية عليها
2. الإجابة على أسئلة الأعضاء في القناة وفي الخاص بأسلوب علمي مبسط
3. ربط الموضوعات بالثقافات المختلفة حول العالم

قواعد مهمة:
- اكتب دائماً بالعربية الفصحى المبسطة
- استخدم الأمثلة الواقعية والمقارنات الثقافية
- كن مختصراً لكن مفيداً (لا تتجاوز 300 كلمة)
- أضف إيموجي مناسبة لتحسين القراءة
- لا تكرر نفس المعلومات من المنشور الأصلي، بل أضف قيمة جديدة"""

def ask_groq(user_message: str, context_message: str = "") -> str:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context_message:
            messages.append({
                "role": "user",
                "content": (
                    f"المنشور الأصلي:\n{context_message}\n\n"
                    f"السؤال أو التفاعل المطلوب:\n{user_message}"
                ),
            })
        else:
            messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"خطأ في Groq: {e}")
        return "عذراً، واجهت مشكلة مؤقتة. الرجاء المحاولة مرة أخرى."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 مرحباً! أنا بوت الأنثروبولوجيا الذكي 🔬\n\n"
        "يمكنك:\n"
        "• سؤالي أي سؤال عن علم الإنسان والأنثروبولوجيا\n"
        "• إرسال أي موضوع تريد فهمه بعمق\n\n"
        "جرب الآن! 👇"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔬 *بوت الأنثروبولوجيا الذكي*\n\n"
        "*ما الذي يمكنني فعله؟*\n"
        "• أرد على منشورات القناة بتحليل أنثروبولوجي\n"
        "• أجيب على أسئلتك في الخاص\n"
        "• أشرح المفاهيم الصعبة ببساطة\n\n"
        "*كيف أستخدمني؟*\n"
        "فقط اكتب سؤالك مباشرة! 💬",
        parse_mode="Markdown",
    )

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    user_name = update.message.from_user.first_name or "عزيزي"
    logger.info(f"[خاص] {user_name}: {user_text[:60]}...")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ask_groq(user_text)
    await update.message.reply_text(
        f"🔬 *تحليل أنثروبولوجي:*\n\n{reply}",
        parse_mode="Markdown",
    )

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    if update.effective_chat.id != DISCUSSION_GROUP_ID:
        return

    msg = update.message
    bot_username = context.bot.username

    is_from_channel = (
        msg.forward_origin is not None or
        (msg.forward_from_chat and str(msg.forward_from_chat.id) == str(CHANNEL_ID))
    )
    if is_from_channel:
        logger.info("منشور قناة في المجموعة — جارِ التحليل...")
        await context.bot.send_chat_action(chat_id=msg.chat_id, action="typing")
        prompt = f"قم بتحليل هذا المنشور الأنثروبولوجي وأضف معلومات وتعليقات ثرية عليه:\n\n{msg.text}"
        reply = ask_groq(prompt)
        await msg.reply_text(
            f"🔬 *تحليل أنثروبولوجي للمنشور الجديد:*\n\n{reply}",
            parse_mode="Markdown",
        )
        return

    is_mention = bot_username and f"@{bot_username}" in msg.text
    is_reply_to_bot = (
        msg.reply_to_message and
        msg.reply_to_message.from_user and
        msg.reply_to_message.from_user.is_bot
    )
    if is_mention or is_reply_to_bot:
        user_text = msg.text.replace(f"@{bot_username}", "").strip() if bot_username else msg.text
        context_text = ""
        if msg.reply_to_message and msg.reply_to_message.text:
            context_text = msg.reply_to_message.text
        if not user_text:
            user_text = "اشرح لي هذا الموضوع"

        logger.info(f"[مجموعة — ذكر] {user_text[:60]}...")
        await context.bot.send_chat_action(chat_id=msg.chat_id, action="typing")
        reply = ask_groq(user_text, context_text)
        await msg.reply_text(f"🔬 {reply}", parse_mode="Markdown")
        return

    question_words = ["ما هي", "ما هو", "كيف", "لماذا", "ماذا", "متى", "أين",
                      "من هم", "ما معنى", "هل", "?", "؟"]
    is_question = any(w in msg.text for w in question_words) and len(msg.text) > 10
    if is_question:
        logger.info(f"[مجموعة — سؤال] {msg.text[:60]}...")
        await context.bot.send_chat_action(chat_id=msg.chat_id, action="typing")
        reply = ask_groq(msg.text)
        await msg.reply_text(f"🔬 {reply}", parse_mode="Markdown")

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.channel_post or not update.channel_post.text:
        return

    post_text = update.channel_post.text
    logger.info(f"منشور قناة جديد: {post_text[:60]}...")

    await context.bot.send_chat_action(chat_id=DISCUSSION_GROUP_ID, action="typing")
    prompt = (
        f"قم بتحليل هذا المنشور الأنثروبولوجي وأضف معلومات وتعليقات "
        f"ثرية وسؤالاً للنقاش:\n\n{post_text}"
    )
    reply = ask_groq(prompt)
    await context.bot.send_message(
        chat_id=DISCUSSION_GROUP_ID,
        text=f"🔬 *تحليل أنثروبولوجي للمنشور الجديد:*\n\n{reply}",
        parse_mode="Markdown",
    )

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("يجب تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")
    if not GROQ_API_KEY:
        raise ValueError("يجب تعيين GROQ_API_KEY في متغيرات البيئة")

    logger.info(f"تشغيل البوت... مجموعة النقاش: {DISCUSSION_GROUP_ID}")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST & filters.TEXT,
        handle_channel_post,
    ))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
        handle_group_message,
    ))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        handle_private_message,
    ))

    logger.info("البوت يعمل الآن ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
