import discord
from discord.ext import commands
import requests
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='#', intents=intents, help_command=None)

# المفاتيح الخاصة بك مدمجة وجاهزة للتشغيل
GEMINI_API_KEY = "AIzaSyCTkQOX4aMBVg5O-4f1ww945oeWlUW4nBM"
DISCORD_TOKEN = "OTg4NjYxMTk4MzY5MjA2Mjgy.GpSbe1.VBV6F7ZfYMI9cKfqlnSdhZWCYX4jLScCk9j1x8"

SYSTEM_INSTRUCTION = """
توجيهات النظام: أنت الآن بوت سيرفر ديسكورد ذكي ومرح اسمه (فدك).
إذا طلب منك أحد المشرفين تنفيذ أمر إداري مثل (الحظر، الطرد، قفل الروم، فتح الروم، مسح الرسائل) بأي صيغة كلامية (مثال: بند ذا، احظره، قفل الشات، نظف الروم)، يجب أن تضع في السطر الأول من ردك الكود البرمجي المناسب للأمر تماماً كالتالي:
- للحظر: cmd_ban
- للطرد: cmd_kick
- لقفل الروم: cmd_lock
- لفتح الروم: cmd_unlock
- لمسح الرسائل: cmd_clear:العدد (مثال cmd_clear:20)

ثم انزل سطراً جديداً واكتب ردك الطبيعي والمرح للعضو. إذا كانت السالفة مجرد كلام عادي ولا يوجد أمر إداري، اكتب ردك الطبيعي فوراً دون إضافة أي كود في السطر الأول.
"""

def ask_gemini_sync(prompt):
    # الرابط المستقر والمدعوم لإنهاء أخطاء الـ 404
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [
            {
                "parts": [{"text": f"{SYSTEM_INSTRUCTION}\nالمستخدم يقول: {prompt}"}]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"📡 استجابة خادم جوجل: {response.status_code} - {response.text}")
            return f"⚠️ خطأ اتصال بجمناي: {response.status_code}"
    except Exception as e:
        return f"❌ خطأ داخلي في الشبكة: {str(e)}"

async def ask_gemini(prompt):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, ask_gemini_sync, prompt)

@bot.event
async def on_ready():
    print("----------------------------------------")
    print(f"🚀 بوت فدك شغال ومستقر الآن ومستعد لتلقي الأوامر!")
    print("----------------------------------------")
    await bot.change_presence(activity=discord.Game(name="يا فدك [للأوامر الذكية]"))

@bot.event
async def on_message(message):
    if message.author.bot: return

    if message.content.startswith('يا فدك') or message.content.startswith('#فدك') or bot.user.mentioned_in(message):
        prompt = message.content.replace('يا فدك', '').replace('#فدك', '').replace(f'<@{bot.user.id}>', '').strip()
        if not prompt:
            await message.channel.send(f"هلا بك {message.author.mention}، آمرني وش بغيت؟ ✨")
            return

        async with message.channel.typing():
            ai_reply = await ask_gemini(prompt)
            lines = ai_reply.split('\n')
            first_line = lines[0].strip()
            
            if first_line.startswith('cmd_'):
                final_text = '\n'.join(lines[1:]).strip()
                
                if first_line == 'cmd_ban':
                    if message.author.guild_permissions.ban_members:
                        target = None
                        if message.reference and message.reference.resolved:
                            target = message.reference.resolved.author
                        else:
                            mentions = [m for m in message.mentions if m.id != bot.user.id]
                            if mentions: target = mentions[0]
                        
                        if target:
                            try:
                                await target.ban(reason=f"أمر ذكي من {message.author.name}")
                                await message.reply(final_text if final_text else f"🔨 أبشر، تم حظر {target.name}")
                            except:
                                await message.reply("❌ فشل الحظر، تأكد أن رتبة البوت أعلى من رتبة العضو!")
                        else:
                            await message.reply("❌ ما قدرت أحدد العضو، منشنه أو رد على رسالته.")
                    else:
                        await message.reply("❌ ما تملك صلاحية الحظر (Ban) بالسيرفر.")
                    return

                elif first_line == 'cmd_kick':
                    if message.author.guild_permissions.kick_members:
                        target = None
                        if message.reference and message.reference.resolved:
                            target = message.reference.resolved.author
                        else:
                            mentions = [m for m in message.mentions if m.id != bot.user.id]
                            if mentions: target = mentions[0]
                        
                        if target:
                            try:
                                await target.kick(reason=f"أمر ذكي من {message.author.name}")
                                await message.reply(final_text if final_text else f"👢 تم طرد {target.name}")
                            except:
                                await message.reply("❌ فشل طرد العضو، تأكد من الرتب.")
                        else:
                            await message.reply("❌ منشن الشخص أو رد على رسالته لطرده.")
                    else:
                        await message.reply("❌ ما عندك صلاحية الطرد (Kick).")
                    return

                elif first_line == 'cmd_lock':
                    if message.author.guild_permissions.manage_channels:
                        await message.channel.set_permissions(message.guild.default_role, send_messages=False)
                        await message.reply(final_text if final_text else "🔒 تم قفل الروم.")
                    else:
                        await message.reply("❌ ما تملك صلاحية إدارة القنوات لقفل الروم.")
                    return

                elif first_line == 'cmd_unlock':
                    if message.author.guild_permissions.manage_channels:
                        await message.channel.set_permissions(message.guild.default_role, send_messages=True)
                        await message.reply(final_text if final_text else "🔓 تم فتح الروم.")
                    else:
                        await message.reply("❌ ما عندك صلاحية لفتح الروم.")
                    return

                elif first_line.startswith('cmd_clear'):
                    if message.author.guild_permissions.manage_messages:
                        try:
                            amount = int(first_line.split(':')[1])
                        except:
                            amount = 10
                        await message.channel.purge(limit=amount + 1)
                        if final_text: await message.channel.send(final_text, delete_after=5)
                    else:
                        await message.reply("❌ ما عندك صلاحية مسح الرسائل.")
                    return

            await message.reply(ai_reply)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)

