import json
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

API_TOKEN = "8750699710:AAEcN9zLD8FZMskYtGx9WQnVT087IocpgAY"
ADMIN_ID = 7888138932

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
DATA_FILE = "movies.json"

MINI_APP_URL = "https://lazikotiktok-source.github.io/dramabox/"

def load_movies():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_movies(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class AddMovie(StatesGroup):
    name = State()
    poster = State()
    video_url = State()

class AddEpisode(StatesGroup):
    video_url = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi film qo'shish", callback_data="add_movie")],
        [InlineKeyboardButton(text="🎬 Kinolarni boshqarish", callback_data="manage_movies")]
    ])
    await message.answer("Salom Admin! Telegram Mini App boti tayyor:", reply_markup=keyboard)

@dp.callback_query(F.data == "add_movie")
async def start_add_movie(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("🎬 Yangi film nomini kiriting:")
    await state.set_state(AddMovie.name)
    await callback.answer()

@dp.message(AddMovie.name)
async def process_movie_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🖼 Endi film uchun rasm (poster) yuboring:")
    await state.set_state(AddMovie.poster)

@dp.message(AddMovie.poster, F.photo)
async def process_movie_poster(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    
    os.makedirs("posters", exist_ok=True)
    poster_filename = f"posters/movie_{len(load_movies()) + 1}.jpg"
    await bot.download_file(file_info.file_path, poster_filename)
    
    await state.update_data(poster=poster_filename)
    await message.answer("🔗 Endi ushbu filmning (1-qism) tayyor .mp4 ssilkasini yuboring:")
    await state.set_state(AddMovie.video_url)

@dp.message(AddMovie.video_url)
async def process_movie_url(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
  
    name = user_data["name"]
    poster = user_data["poster"]
    video_url = message.text.strip()
    
    movies = load_movies()
    movie_key = f"movie_{len(movies) + 1}"
    movies[movie_key] = {
        "title": name,
        "poster": poster,
        "episodes": [{"name": "1-qism", "url": video_url}]
    }
    save_movies(movies)
    await state.clear()
    
    app_link = f"{MINI_APP_URL}?movie={movie_key}&ep=0"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Kinoni ko'rish (Mini App)", web_app=WebAppInfo(url=app_link))]
    ])
    
    await message.answer(
        f"✅ <b>{name}</b> 1-qism Mini App'ga muvaffaqiyatli qo'shildi!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "manage_movies")
async def manage_movies(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    movies = load_movies()
    if not movies:
        await callback.message.answer("Hozircha kinolar yo'q.")
        await callback.answer()
        return
    buttons = [[InlineKeyboardButton(text=m["title"], callback_data=f"edit_{k}")] for k, m in movies.items()]
    buttons.append([InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="main_menu")])
    await callback.message.answer("Qaysi filmga o'zgartirish kiritmoqchisiz?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def back_main_menu(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi film qo'shish", callback_data="add_movie")],
        [InlineKeyboardButton(text="🎬 Kinolarni boshqarish", callback_data="manage_movies")]
    ])
    await callback.message.answer("Asosiy menyu:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_"))
async def edit_movie(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    full_key = callback.data.replace("edit_", "")
    movies = load_movies()
    movie = movies.get(full_key)
    if not movie:
        await callback.message.answer("Film topilmadi.")
        await callback.answer()
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi qism qo'shish", callback_data=f"add_ep_{full_key}")],
        [InlineKeyboardButton(text="🗑 Kinoni o'chirish", callback_data=f"del_{full_key}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="manage_movies")]
    ])
    await callback.message.answer(f"🎬 <b>{movie['title']}</b>\nQismlar soni: {len(movie['episodes'])} ta", reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("add_ep_"))
async def start_add_episode(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    full_key = callback.data.replace("add_ep_", "")
    await state.update_data(current_movie=full_key)
    await callback.message.answer("🔗 Yangi qismning .mp4 ssilkasini yuboring:")
    await state.set_state(AddEpisode.video_url)
    await callback.answer()

@dp.message(AddEpisode.video_url)
async def process_episode_url(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    user_data = await state.get_data()
    movie_key = user_data["current_movie"]
    video_url = message.text.strip()
    movies = load_movies()
    if movie_key in movies:
        ep_index = len(movies[movie_key]["episodes"])
        ep_count = ep_index + 1
        new_ep_name = f"{ep_count}-qism"
        movies[movie_key]["episodes"].append({"name": new_ep_name, "url": video_url})
        save_movies(movies)
        
        app_link = f"{MINI_APP_URL}?movie={movie_key}&ep={ep_index}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"▶️ {new_ep_name} ni ko'rish (Mini App)", web_app=WebAppInfo(url=app_link))]
        ])
        
        await message.answer(
            f"✅ <b>{new_ep_name}</b> qo'shildi!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await state.clear()

@dp.callback_query(F.data.startswith("del_"))
async def delete_movie(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    full_key = callback.data.replace("del_", "")
    movies = load_movies()
    if full_key in movies:
        title = movies[full_key]["title"]
        del movies[full_key]
        save_movies(movies)
        await callback.message.answer(f"🗑 '{title}' o'chirildi!")
    await callback.answer()

if __name__ == "__main__":
    import asyncio
    print("Mini App boti ishga tushdi...")
    asyncio.run(dp.start_polling(bot))
