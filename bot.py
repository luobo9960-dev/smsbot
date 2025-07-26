# bot.py
import asyncio
import time
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import BOT_TOKEN, API_URL, SMS_KEYWORD, SMS_POLL_INTERVAL, SMS_POLL_TIMEOUT
from redis_helper import redis_helper

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(bot)

# —————— Token 缓存 & 刷新 ——————
async def get_token(session: aiohttp.ClientSession) -> str:
    """
    优先从 Redis 获取 token；若不存在或失效，调用登录接口刷新并缓存 6 小时。
    """
    token = await redis_helper.get("api_token")
    if token:
        return token

    # 调用 login 接口
    params = {"code": "login", "user": "<用户名>", "password": "<密码>"}
    async with session.get(API_URL, params=params) as resp:
        text = await resp.text()
    if text.startswith("ERROR:"):
        raise RuntimeError(f"登录失败：{text}")
    token = text.strip()
    # 缓存 6 小时
    await redis_helper.set("api_token", token, expire=6*3600)
    return token

# —————— 核心命令：/getphone ——————
@dp.message_handler(commands=["getphone"])
async def cmd_getphone(msg: types.Message):
    """
    支持 三种模式：实卡、虚卡、随机；或用户指定 phone 参数。
    """
    kb = InlineKeyboardMarkup().row(
        InlineKeyboardButton("实卡", callback_data="cardType=实卡"),
        InlineKeyboardButton("虚卡", callback_data="cardType=虚卡"),
        InlineKeyboardButton("随机", callback_data="cardType=全部"),
    )
    await msg.reply("请选择卡类型：", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("cardType"))
async def cb_getphone(callback: types.CallbackQuery):
    card_type = callback.data.split("=")[1]
    await callback.answer(f"正在获取{card_type}号码…")
    async with aiohttp.ClientSession() as session:
        try:
            token = await get_token(session)
            params = {"code": "getPhone", "token": token, "cardType": card_type}
            # 如需指定省份或号码，可在 params 中添加 "province"/"phone"
            async with session.get(API_URL, params=params) as resp:
                phone = (await resp.text()).strip()
            if phone.startswith("ERROR:"):
                raise RuntimeError(phone)
        except Exception as e:
            return await callback.message.reply(f"取号失败：{e}")
    # 保存到 Redis，供 getMsg 轮询使用，1 小时后过期
    await redis_helper.set(f"phone:{callback.from_user.id}", phone, expire=3600)
    await callback.message.reply(f"✅ 获取到号码：`{phone}`\n请等待短信…", parse_mode="Markdown")

# —————— 核心命令：/getcode ——————
@dp.message_handler(commands=["getcode"])
async def cmd_getcode(msg: types.Message):
    """
    轮询 getMsg，直到超时或取到包含关键词的短信；最后自动释放号码。
    """
    phone = await redis_helper.get(f"phone:{msg.from_user.id}")
    if not phone:
        return await msg.reply("未找到可用号码，请先执行 /getphone")
    await msg.reply("开始获取验证码…")

    async with aiohttp.ClientSession() as session:
        token = await get_token(session)
        deadline = time.time() + SMS_POLL_TIMEOUT
        code_text = None
        while time.time() < deadline:
            params = {
                "code": "getMsg", "token": token,
                "phone": phone, "keyWord": SMS_KEYWORD
            }
            async with session.get(API_URL, params=params) as resp:
                text = await resp.text()
            if not text.startswith("[尚未收到]"):
                code_text = text.strip()
                break
            await asyncio.sleep(SMS_POLL_INTERVAL)

        # 超时或取到
        if not code_text:
            await msg.reply("⌛ 获取超时，请稍后重试或更换号码。")
        else:
            await msg.reply(f"🎉 收到短信：`{code_text}`", parse_mode="Markdown")
        # 释放号码
        await session.get(API_URL, params={"code": "release", "token": token, "phone": phone})

if __name__ == "__main__":
    async def main():
        await redis_helper.init_pool()
        await dp.start_polling()
        await redis_helper.close()

    asyncio.run(main())
