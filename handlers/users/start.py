from aiogram.filters import CommandStart
from loader import dp, db, bot
from aiogram import types, F
from keyboards.default.buttons import start_button, kargo_type, client_button, get_phone_number_button, skip_button, \
    admin_button
from aiogram.fsm.context import FSMContext
from states.my_state import Register
from keyboards.inline.buttons import check_button, CheckCall, signup, region_button, prog
import uuid
import random
import asyncio
from aiogram.utils.keyboard import InlineKeyboardBuilder
from filters.admin_filter import Admin, Member, AdminMember
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import os
from data.config import SEO
from aiogram import exceptions


def fix():
    btn = ReplyKeyboardBuilder()
    btn.button(text='♻️ Botni ishga tushurish', request_contact=True)
    btn.adjust(2)  # Tugmalarni ikki ustun qilib joylashtiradi
    return btn.as_markup(resize_keyboard=True, one_time_keyboard=True)

@dp.message(CommandStart(), AdminMember())
async def start_bot(message: types.Message):
    if db.select_user(telegram_id=message.from_user.id):
        await message.answer(f"Assalamu Aleykum {message.from_user.full_name}", reply_markup=client_button())
    else:
        await message.answer("Bot ishga tushishi uchun bosing:", reply_markup=fix())




@dp.message(CommandStart(), Admin())
async def start_admin_bot(message: types.Message):
    await message.answer(f"Assalomu alaykum xurmatli {message.from_user.full_name}! saja jamosiga xush kelibsiz "
                             f" Botimizga xush kelibsiz", reply_markup=admin_button())


@dp.callback_query(lambda query: query.data.startswith('register'))
async def get_name(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Ism va Familyangizni kiriting:")
    await call.answer(cache_time=60)
    await state.set_state(Register.name)


@dp.message(F.text, Register.name)
async def get_phone(msg: types.Message, state: FSMContext):
    name = msg.text
    await state.update_data({"name": name})
    await msg.answer(f"Telefon raqamingizni yuboring:", reply_markup=get_phone_number_button())
    await state.set_state(Register.phone)


@dp.message(F.contact, Register.phone)
async def get_contact(message: types.Message, state: FSMContext):
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
        await state.update_data({"phone": phone})
        await message.answer(f"Qo'shimcha telefon raqamingizni kiriting: Masalan: +9981234567",
                             reply_markup=skip_button())
        await state.set_state(Register.phone_number)
    else:
        await message.answer("Telefon raqamini ulashishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


@dp.message(F.text, Register.phone_number)
async def get_address(msg: types.Message, state: FSMContext):
    phone_number = msg.text
    if phone_number == "◀️ O'tkazib Yuborish":
        phone_number = None
    await state.update_data({"phone_number": phone_number})
    await msg.answer("Viloyatni tanlang", reply_markup=region_button())
    await state.set_state(Register.address)


@dp.callback_query(lambda query: query.data.startswith('region_'), Register.address)
async def get_districts(call: types.CallbackQuery, state: FSMContext):
    region_name = call.data.split('_')[-1].capitalize()
    data = db.select_address(region_name=region_name)
    if not data:
        await call.answer("Region topilmadi.")
        return

    region_id = data[2]
    datas = db.select_district_names_by_region_id(region_id=region_id)
    btn = InlineKeyboardBuilder()

    for district in datas:
        btn.button(text=district, callback_data=f"district_{district}")

    btn.adjust(2)
    await state.update_data({"region": region_name})
    await call.message.edit_text("Tumanlarni tanlang:", reply_markup=btn.as_markup())
    await state.set_state(Register.district)

@dp.callback_query(lambda query: query.data.startswith('district_'), Register.district)
async def get_exact_address(call: types.CallbackQuery, state: FSMContext):
    district_name = call.data.split('_')[-1]
    await state.update_data({"district": district_name})
    await call.answer(cache_time=60)
    await call.message.answer(f"Tumanni tanladingiz: {district_name}: Endi aniq manzil kiriting:"
                              f"Masalan {district_name} Alisher N kochasi 17 uy")
    await state.set_state(Register.exact_address)

@dp.message(F.text, Register.exact_address)
async def get_kargo(message: types.Message, state: FSMContext):
    exact_address = message.text
    await state.update_data(
        {
            "exact_address": exact_address
        }
    )
    await message.answer(f"Endi kargo turini tanlang:", reply_markup=kargo_type())
    await state.set_state(Register.Kargo)


@dp.message(F.text.in_(['🚚 Auto', '✈️ Avia']), Register.Kargo)
async def get_description(msg: types.Message, state: FSMContext):
    kargo = msg.text
    await state.update_data({"kargo": kargo})
    await msg.answer(F"Qoshimcha malumot kiriting:")
    await state.set_state(Register.description)


@dp.message(F.text, Register.description)
async def final(msg: types.Message, state: FSMContext):
    description = msg.text
    await state.update_data({"description": description})
    data = await state.get_data()

    phone_number = data.get('phone_number')

    text = f"📑 Ushbu ma'lumotlar to'g'rimi?\n"
    text += f"📌 Ism Familya: {data.get('name', 'N/A')}\n"
    text += f"☎️ Telefon Raqam: {data.get('phone', 'N/A')}\n"
    if phone_number:
        text += f"☎️ Qo'shimcha Telefon Raqam: {phone_number}\n"
    text += f"🖼 Viloyat: {data.get('region', 'N/A')}\n"
    text += f"🏙 Tuman: {data.get('district', 'N/A')}\n"
    text += f"🚪 Aniq Manzil: {data.get('exact_address', 'N/A')}\n"
    text += f"📦 Kargo turi: {data.get('kargo', 'N/A')}\n"
    text += f"📝 Qoshimcha Ma'lumot: {data.get('description', 'N/A')}"
    await msg.answer(text=text, reply_markup=check_button())
    await state.set_state(Register.check)


@dp.callback_query(CheckCall.filter(), Register.check)
async def check_data(call: types.CallbackQuery, callback_data: CheckCall, state: FSMContext):
    check = callback_data.check
    await call.answer(cache_time=60)

    while True:
        user_ids = random.randint(100000, 999999)

        # Fayldan count o'qish
        with open('count.txt', 'r') as file:
            count = int(file.read().strip())

        saja_value = f'SAJA-{count}'
        sj_avia_value = f'SJ-avia-{count}'
        existing_saja = db.select_user_by_saja_value(saja_value)
        existing_sj_avia = db.select_user_by_sj_avia_value(sj_avia_value)

        if not existing_saja and not existing_sj_avia:
            # `count`ni yangilash faqat `check` True bo'lsa
            if check:
                new_count = count + 1
                with open('count.txt', 'w') as file:
                    file.write(str(new_count))
            break

    if check:
        data = await state.get_data()
        user_id = str(uuid.uuid4())
        fullname = data['name']
        telegram_id = call.from_user.id
        language = call.from_user.language_code
        phone = data['phone']
        phone_number = data['phone_number']
        manzil = data['region']
        tuman = data['district']
        kargo = data['kargo']
        exact_address = data['exact_address']
        description = data['description']
        saja = saja_value if kargo == '🚚 Auto' else None
        sj_avia = sj_avia_value if kargo == '✈️ Avia' else None

        db.add_user(
            id=user_id,
            fullname=fullname,
            telegram_id=telegram_id,
            language=language,
            phone=phone,
            phone_number=phone_number,
            manzil=manzil,
            tuman=tuman,
            saja=saja,
            sj_avia=sj_avia,
            exact_address=exact_address,
            description=description,
            user_id=user_ids
        )
        await call.message.answer("Muvaffaqiyatli ro'yxatdan o'tdingiz 👏", reply_markup=client_button())
        data = db.get_users_by_activation_status1()

        if not data:
            await call.message.answer("Hozirda userlar ma'lumoti mavjud emas !!!")
            return

        users_data = []

        for user in data:
            user_info = {
                "Ism Familyasi": user[1],
                "Phone": user[4],
                "Manzil": user[6],
                "Tuman": user[9],
                "Aniq Manzil": user[11],
                "Qoshimcha Ma'lumot": user[12],
                "User ID": user[13],
                "Qo'shilgan vaqt": user[-2],
                "Telegram ID": user[2]
            }

            user_info["Phone Number"] = user[5] if user[5] else None
            user_info["SAJA"] = user[7] if user[7] else None
            user_info["SAJA Avia"] = user[8] if user[8] else None

            users_data.append(user_info)

        import xlsxwriter

        file_path = "users_lists.xlsx"
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()

        headers = list(users_data[0].keys())
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        for row_num, user_info in enumerate(users_data, 1):  # 1-dan boshlanadi, 0-ustun nomlari uchun
            for col_num, (key, value) in enumerate(user_info.items()):
                worksheet.write(row_num, col_num, value)

        # Excel faylini saqlash
        workbook.close()

        # Excel faylini jo'natish
        excel_file = types.InputFile(file_path)
        for i in SEO:
            try:
                await bot.send_document(chat_id=int(i), document=excel_file,
                                        caption="Foydalanuvchilar ma'lumotlari Excel faylda")
            except exceptions.TelegramBadRequest as e:
                print(f"Xatolik: {e}. Chat ID: {i}")

        if os.path.isfile(file_path):
            os.remove(file_path)
    else:
        await call.message.answer("Qaytadan ro'yxatdan o'ting\n"
                                  "/start")
        await call.message.delete()

    await asyncio.sleep(5)
    await state.clear()

@dp.message(F.text == '📬 Buyurtmalarim', Member())
async def user_orders(message: types.Message):
    user_data = db.select_user(telegram_id=message.from_user.id)
    print("User Data:", user_data)

    if not user_data:
        await message.answer("Foydalanuvchi topilmadi.")
        return

    saja_id = user_data[7]
    saja_id1 = user_data[6]

    if saja_id1:
        saja_id_str = 'SAJA-{}'.format(saja_id[-3:])
        orders = db.select_orders_by_saja_id(saja_id=saja_id_str)
    elif saja_id:
        saja_id_str = 'SJ-avia-{}'.format(saja_id1[-3:])
        orders = db.select_orders_by_saja_id(saja_id=saja_id_str)
    else:
        orders = []

    if orders:
        order_list = []
        for order in orders:
            order_list.append(
                "Buyurtma ID: {}\n"
                "Client ID: {}\n"
                "Buyurtma miqdori: {}\n"
                "Narxi: {}\n"
                "Status: {}\n\n".format(
                    order[-1],
                    order[1],
                    order[2],
                    order[5],
                    '🟩 To\'langan' if order[6] == 1 else '🟧 To\'lanmagan'
                )
            )
        await message.answer("Buyurtmalaringiz:\n\n" + "".join(order_list))
    else:
        await message.answer("❌ Sizda hech qanday buyurtma mavjud emas.")


@dp.message(F.text == '☎️ Aloqa', Member())
async def get_call(message: types.Message):
    text = """
    Aloqa Bo'limi 📞
    Adminlar:
    @saja_kargo_admin
    @saja_express_admin2
    
    Hamkorlik uchun:
    @saja_express
    
    Telegram kanal:
    @saja_express_kargo
    """
    await message.answer(text=text)


# @dp.message(F.text == '➕ Buyurtma berish', Member())
# async def get_call(message: types.Message):
#     text = """
#     SAJA EXPRESS🦁
#     🚚Avto kargosi ishlash tartibi bilan tanishib chiqing.
#
#     🌐Yuklar xitoy skladimizdan haftasiga 2 marta jo’natiladi va
#      jo’natilgan kundan boshlab 14_18kun ichida yetib keladi.✔️
#     🔖Yetib kelganligi haqida shu @saja_express_kargo telegram
#      kanalda e’lon qilamiz. Viloyatlarga 48 soat ichida
#         yetkazib beramiz.⌛
#     📍O’zbekistonning barcha tumanlariga pochta yuklarini bepul
#         yetkazib beramiz.🆓✔️
#
#
#     💵Narxlar💵
#
#     💵50 kggacha 7.5$ dan kilosiga
#
#
#     ✈️Avia kargo ishlash tartibi bilan tanishib chiqing.
#
#     5_7 kunda keladi
#
#     💵Narxi, 11$ kilosiga
#
#     💡KATTA MIQDORDAGI VA TIJORAT YUKLARI (zapchast, texnika,
#     stanok, seriyali…)KELISHUV ASOSIDA☄️➡️@saja_express⬅️
#
#     💯Minimalka yo’q💯
#     Agarda mahsulotingiz 100g bo’lsa, faqat shu vaznga
#     pul to’laysiz⚡️
#
#     Qanday qilib xitoy online platformalari
#      (tao bao, pinduoduo, 1688)
#     0 dan mustaqil ravishda buyurtma qilishni o'rganasiz
#     @saja_express_kurator
#     """
#     await message.answer(text=text)

@dp.message(F.text == '➕ Buyurtma berish', Member())
async def get_call(message: types.Message):
    text = """
    Xitoydagi omborimiz manzili:
    SAJA-***

    15200815181
    
    广东省广州市白云区白云湖街道
    
    夏茅村南约路针车城 143档口 SAJA-***

    """
    await message.answer(text=text, reply_markup=prog())


@dp.callback_query(lambda query: query.data == 'prog')
async def get_prog(call: types.CallbackQuery):
    await call.answer(cache_time=60)


    image1 = types.input_file.FSInputFile(path='images/tao.jpg')
    image2 = types.input_file.FSInputFile(path='images/tao1.jpg')
    media = MediaGroupBuilder(caption="Taobao uchun")
    media.add_photo(type='photo', media=image1)
    media.add_photo(type='photo', media=image2)



    image3 = types.input_file.FSInputFile(path='images/pin.jpg')
    image4 = types.input_file.FSInputFile(path='images/pin1.jpg')
    media_pin = MediaGroupBuilder(caption="Pinduoduo uchun")
    media_pin.add_photo(type='photo', media=image3)
    media_pin.add_photo(type='photo', media=image4)



    image5 = types.input_file.FSInputFile(path='images/on.jpg')
    image6 = types.input_file.FSInputFile(path='images/on1.jpg')
    media_on = MediaGroupBuilder(caption="1688 uchun")
    media_on.add_photo(type='photo', media=image5)
    media_on.add_photo(type='photo', media=image6)

    await call.message.answer_media_group(media=media.build())
    await call.message.answer_media_group(media=media_pin.build())
    await call.message.answer_media_group(media=media_on.build())

@dp.message(F.contact)
async def get_phone_number(message: types.Message):
    if message.contact:
        phone = message.contact.phone_number
        if db.select_user(phone=phone):
            await message.answer(f"Assalamu Aleykum {message.from_user.full_name}", reply_markup=client_button())
            db.update_user_field_phone(field="telegram_id", phone=phone, value=message.from_user.id)
        else:
            await message.answer(f"Assalomu alaykum {message.from_user.full_name}!"
                                 f" Botimizga xush kelibsiz", reply_markup=signup())
    else:
        await message.answer("Telefon raqami olinmadi, iltimos qaytadan urinib ko'ring.")