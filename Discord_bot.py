import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
import json
import os
import random
import datetime

import aiohttp
from aiohttp import web

async def health_check(request):
  return web.Response(text="OK", status=200)

async def start_web_server():
  app = web.Application()
  app.router.add_get('/health', health_check) # Health Check API 추가
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, '0.0.0.0', 8000)
  await site.start()

import aiohttp
from aiohttp import web

async def health_check(request):
  return web.Response(text="OK", status=200)

async def start_web_server():
  app = web.Application()
  app.router.add_get('/health', health_check) # Health Check API 추가
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, '0.0.0.0', 8000)
  await site.start()

# --- 설정 ---
# ⚠️ 주의: 봇을 실행하기 전에 아래 'YOUR_BOT_TOKEN' 부분을 실제 봇 토큰으로 교체하세요.
TOKEN = "MTQwOTc5NTgwMDQwNTYzOTMwMQ.G-uNj_.sU8b3q7ZTWuhy3F6vfucEADqIDrt8i7nyig6Vs"
DATA_FILE = "data.json"
LOG_FILE = "bot_log.json"

# ⭐⭐ 사용자 지정 설정 ⭐⭐
#Discord ID를 여기에 넣어, 이 ID만 관리자 권한을 갖도록 설정
OWNER_IDS = ["925603847269937183", "1266001399838146675"]
ADMIN_IDS = ["925603847269937183", "1406986519587328080", "1266001399838146675", "1281901747870109706",
             "1160542995863576646"]
WHITELIST_IDS = ["925603847269937183", "1406986519587328080", "1266001399838146675", "1281901747870109706",
             "1160542995863576646", "1294462091725508610", "1038769191903305748", "1342787003481063515"]

# 송금 수수료 (고정 차감)
TRANSFER_FEE = 2
# 🌟 신규/수정 기능 설정
ATTENDANCE_REWARD = 1  # 출석 체크 기본 보상 포인트
DAILY_BONUS_REWARD = 3  # 7회 연속 출석 시 추가 보너스 포인트
DAILY_BONUS_COUNT = 7  # 연속 출석 보너스를 받을 횟수
LEVEL_UP_COST = 10  # 레벨업에 필요한 포인트 비용


# ===== 봇 클래스 =====
class MyBot(discord.Client):
    def __init__(self):
        # 메시지 내용, 멤버 정보 접근을 위한 Intenta 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # 슬래시 명령어 동기화
        await self.tree.sync()
        print("✅ 슬래시 명령어 동기화 완료")

    async def on_ready(self):
        # 봇이 준비되었을 때 실행
        print(f"🤖 봇 로그인: {self.user.name} (ID: {self.user.id})")
        # 현재 시간과 상태 출력
        print(f"⏰ 현재 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 30)


bot = MyBot()


# ===== 데이터 로드 / 저장 =====
def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        default_data = {
            "points": {},  # 실제 포인트
            "earned_points": {},  # 차감되지 않은 총 획득 포인트
            "shop": {},
            "inventory": {},
            "attendance": {},  # 출석체크 데이터 (uid: {'last_date': 'YYYY-MM-DD', 'streak': 0})
            "level": {}  # 레벨링 데이터 (uid: 레벨)
        }
        try:
            with open(DATA_FILE, "w", encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ 데이터 파일 생성 중 오류 발생: {e}")
        return default_data
    try:
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ data.json 파일 로드 중 오류 발생 (JSON 디코딩 오류): {e}. 기본 데이터를 사용합니다.")
        return load_data()


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ 데이터 저장 중 오류 발생: {e}")


data = load_data()


# ===== 로그 저장 =====
def log_command(command, user, amount=None, extra=None):
    log = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "command": command,
        "user": user,
        "amount": amount,
        "extra": extra
    }
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        logs = []
    else:
        try:
            with open(LOG_FILE, "r", encoding='utf-8') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []

    logs.append(log)
    try:
        with open(LOG_FILE, "w", encoding='utf-8') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"⚠️ 로그 파일 저장 중 오류 발생: {e}")


def log_point_usage(user, amount, reason):
    # 포인트 사용(차감) 로그를 기록합니다.
    log_command("포인트사용", user, amount, reason)


# ===== 유틸 함수 =====
def is_owner(interaction: discord.Interaction) -> bool:
    # interaction.user가 discord.Member 객체라고 가정합니다.
    user_id_str = str(interaction.user.id)
    # 봇이 관리자 권한을 가진 경우만 허용
    return user_id_str in OWNER_IDS

def is_admin(interaction: discord.Interaction) -> bool:
    # interaction.user가 discord.Member 객체라고 가정합니다.
    user_id_str = str(interaction.user.id)
    # 봇이 관리자 권한을 가진 경우만 허용
    return user_id_str in ADMIN_IDS

def is_whitelist(interaction: discord.Interaction) -> bool:
    # interaction.user가 discord.Member 객체라고 가정합니다.
    user_id_str = str(interaction.user.id)
    # 봇이 관리자 권한을 가진 경우만 허용
    return user_id_str in WHITELIST_IDS


def get_user_points(uid: str) -> int:
    return data["points"].get(uid, 0)


def get_user_total_earned(uid: str) -> int:
    return data.get("earned_points", {}).get(uid, 0)


# 🌟 유저 레벨 가져오기 (수동 레벨링)
def get_user_level(uid: str) -> int:
    return data["level"].get(uid, 1)


# ===== 자동완성 =====
async def shop_item_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    items = data["shop"].keys()
    return [app_commands.Choice(name=i, value=i) for i in items if current.lower() in i.lower()][:25]


async def role_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    roles = [r for r in interaction.guild.roles if r.name != "@everyone" and not r.managed]
    return [app_commands.Choice(name=r.name, value=str(r.id)) for r in roles if current.lower() in r.name.lower()][:25]


# ===== 1. 포인트 관련 =====
@bot.tree.command(name="전체지급", description="모든 서버 사용자에게 포인트를 지급합니다. (관리자 전용)")
@app_commands.describe(
    amount="지급할 포인트 금액을 입력하세요."
)
async def give_all_points(interaction: discord.Interaction, amount: int):
    uid = str(interaction.user.id)

    # 1. 관리자 권한 확인 (제공해주신 ADMIN_IDS 사용)
    if uid not in ADMIN_IDS:
        return await interaction.response.send_message("❌ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)

    # 2. 금액 유효성 검사
    if amount <= 0:
        return await interaction.response.send_message("❌ 지급 금액은 1점 이상이어야 합니다.", ephemeral=True)

    # 3. Deferred 응답
    await interaction.response.defer(ephemeral=False)

    # 4. 모든 사용자에게 포인트 지급 로직
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("❌ 이 명령어는 서버 내에서만 사용할 수 있습니다.")
        return

    member_count = 0

    # 서버 멤버 목록을 순회하며 포인트 지급
    for member in guild.members:
        # 봇 자신에게는 지급하지 않음
        if member.bot:
            continue

        target_uid = str(member.id)

        # 포인트 갱신 (없으면 0점에서 시작)
        current_points = data["points"].get(target_uid, 0)
        data["points"][target_uid] = current_points + amount

        member_count += 1

    # 5. 데이터 저장
    save_data(data)

    # 6. 관리자 로그 기록
    total_points = amount * member_count
    log_command("전체지급", interaction.user.display_name, total_points, f"{member_count}명에게 {amount}점씩 일괄 지급")

    # 7. 응답 메시지 전송
    embed = discord.Embed(
        title="💸 전체 포인트 지급 완료",
        description=f"✅ 관리자 **{interaction.user.display_name}**님이 전체 포인트를 지급했습니다.",
        color=discord.Color.green()
    )
    embed.add_field(name="지급 포인트 (1인당)", value=f"**{amount}점**", inline=False)
    embed.add_field(name="지급 대상 인원", value=f"**{member_count}명**", inline=True)
    embed.add_field(name="총 지급된 포인트", value=f"**{total_points}점**", inline=True)
    embed.set_footer(text=f"작업 완료 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="포인트조회", description="내 포인트 확인")
async def check_points(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    points = get_user_points(uid)
    total_earned = get_user_total_earned(uid)

    # 🌟 레벨 정보 추가
    level = get_user_level(uid)

    await interaction.response.send_message(
        f"💰 {interaction.user.display_name}님의 **현재 포인트**: **{points}점**, 총 획득 포인트: **{total_earned}점**\n"
        f"⭐ **현재 레벨**: **Lv.{level}**"
    )


@bot.tree.command(name="포인트지급", description="유저에게 포인트 지급 (관리자 전용)")
@app_commands.describe(user="포인트를 받을 유저", amount="지급할 포인트 수")
async def give_points(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not is_whitelist(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)
    if amount <= 0:
        return await interaction.response.send_message("❌ 포인트는 0보다 커야 합니다.", ephemeral=True)

    uid = str(user.id)
    # 실제 포인트
    data["points"][uid] = get_user_points(uid) + amount
    # 차감되지 않은 총 획득 포인트
    data.setdefault("earned_points", {})
    data["earned_points"][uid] = data["earned_points"].get(uid, 0) + amount

    save_data(data)
    log_command("포인트지급", interaction.user.display_name, amount, f"대상: {user.display_name}")
    await interaction.response.send_message(
        f"✅ {user.display_name}에게 **{amount}**포인트 지급 완료 (현재: {data['points'][uid]}점)")


@bot.tree.command(name="포인트삭제", description="유저의 포인트를 지정한 숫자만큼 차감합니다. (관리자 전용)")
@app_commands.describe(user="포인트를 차감할 유저", amount="차감할 포인트 수 (양수로 입력)")
async def remove_points(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not is_whitelist(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)
    if amount <= 0:
        return await interaction.response.send_message("❌ 차감할 포인트는 0보다 커야 합니다.", ephemeral=True)

    uid = str(user.id)
    current_points = get_user_points(uid)

    if current_points == 0:
        return await interaction.response.send_message(f"❌ {user.display_name}님은 현재 포인트가 없습니다.", ephemeral=True)

    # 차감 후 포인트 계산 (음수가 될 수도 있음)
    new_points = current_points - amount

    # 포인트 데이터 업데이트
    data["points"][uid] = new_points
    save_data(data)

    log_point_usage(user.display_name, amount, f"관리자 차감")  # 포인트 사용 로그에 차감 기록
    log_command("포인트차감(관리자)", interaction.user.display_name, -amount, f"대상: {user.display_name}, 차감 후: {new_points}")

    await interaction.response.send_message(
        f"✅ {user.display_name}님의 포인트 **{amount}점** 차감 완료.\n"
        f"➡️ **남은 포인트**: **{new_points}점**"
    )

from discord.ui import View, Button

# 🚨 외부 종속성 (실제 봇 파일에 맞게 정의 필요) 🚨
# 예:
# bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
# data = {"points": {}, "earned_points": {}}
# def get_user_points(uid): ...
# def save_data(data_obj): ...
# def log_command(type, user, change, choice): ...
# ----------------------------------------------

# 🚨 외부 종속성 (실제 봇 파일에 맞게 정의 필요) 🚨
# bot 인스턴스, data 딕셔너리, get_user_points, save_data, log_command 함수 정의 필요.
# ----------------------------------------------

# 베팅 포인트를 저장할 딕셔너리 (메시지 ID가 key)
active_games = {}


# --- 뷰 정의 ---

# ===== 2단계: 도전자 베팅 및 결과 처리 View =====
class ChallengeView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="도전 (홀)", style=discord.ButtonStyle.primary)
    async def challenge_odd(self, button_interaction: discord.Interaction, button: Button):
        await self.handle_challenge(button_interaction, "홀")

    @discord.ui.button(label="도전 (짝)", style=discord.ButtonStyle.success)
    async def challenge_even(self, button_interaction: discord.Interaction, button: Button):
        await self.handle_challenge(button_interaction, "짝")

    async def handle_challenge(self, button_interaction: discord.Interaction, challenger_choice: str):
        # 1. 메시지 ID를 사용하여 게임 데이터 조회
        message_id = button_interaction.message.id
        if message_id not in active_games:
            await button_interaction.response.send_message("❌ 이 게임은 만료되었거나 이미 종료되었습니다.", ephemeral=True)
            self.stop()
            return

        game_data = active_games[message_id]

        challenger_id = str(button_interaction.user.id)
        initiator_id = game_data['initiator_id']
        bet = game_data['bet_amount']

        # 2. 동일 유저(명령어 실행자) 베팅 방지
        if challenger_id == initiator_id:
            return await button_interaction.response.send_message("❌ 당신이 만든 게임에는 도전할 수 없습니다.", ephemeral=True)

        # 3. 이미 도전한 유저 베팅 방지 (단일 도전)
        if game_data['challenged']:
            return await button_interaction.response.send_message("❌ 이 게임은 이미 다른 도전자와 종료되었습니다.", ephemeral=True)

        # 4. 포인트 체크 (도전자)
        if get_user_points(challenger_id) < bet:
            return await button_interaction.response.send_message(f"❌ 도전에 필요한 포인트 **{bet}점**이 부족합니다.", ephemeral=True)

        # 5. Defer (지연)
        await button_interaction.response.defer()

        # 6. 개설자 이름 조회 및 결과 계산
        initiator_choice = game_data['initiator_choice']

        initiator_user = button_interaction.guild.get_member(int(initiator_id))
        initiator_name = initiator_user.display_name if initiator_user else "알 수 없는 사용자"

        # --- 포인트 계산 ---
        if challenger_choice == initiator_choice:
            win = bet

            data["points"][challenger_id] = data["points"].get(challenger_id, 0) + win
            data["points"][initiator_id] = data["points"].get(initiator_id, 0) - win

            log_command("홀짝도전(승)", button_interaction.user.display_name, win, f"{challenger_choice} 선택")
            log_command("홀짝베팅(패)", initiator_name, -win, f"{initiator_choice} 선택")

            result_msg = f"🎉 **{button_interaction.user.display_name}**님 ({challenger_choice}) **성공!**\n> 베팅: **{bet}점** 획득! (현재: {data['points'].get(challenger_id, 0)}점)\n> **{initiator_name}**님 ({initiator_choice}) **{bet}점** 손실."
            final_content = f"✅ **게임 종료:** {initiator_name}님의 게임에 {button_interaction.user.display_name}님이 도전하여 **승리**했습니다.\n\n"
        else:
            lose = bet

            data["points"][challenger_id] = data["points"].get(challenger_id, 0) - lose
            data["points"][initiator_id] = data["points"].get(initiator_id, 0) + lose

            log_command("홀짝도전(패)", button_interaction.user.display_name, -lose, f"{challenger_choice} 선택")
            log_command("홀짝베팅(승)", initiator_name, lose, f"{initiator_choice} 선택")

            result_msg = f"😂 **{button_interaction.user.display_name}**님 ({challenger_choice}) **실패!**\n> 베팅: **{lose}점** 손실! (현재: {data['points'].get(challenger_id, 0)}점)\n> **{initiator_name}**님 ({initiator_choice}) **{lose}점** 획득."
            final_content = f"❌ **게임 종료:** {initiator_name}님의 게임에 {button_interaction.user.display_name}님이 도전하여 **패배**했습니다.\n\n"

        save_data(data)

        # 버튼 비활성화 및 원본 메시지 수정
        for item in self.children:
            item.disabled = True

        await button_interaction.edit_original_response(
            content=final_content + result_msg,
            view=self
        )

        if message_id in active_games:
            del active_games[message_id]

        self.stop()

    async def on_timeout(self):
        # self.message가 할당되었으므로 이제 오류 없이 동작해야 합니다.
        message_id = self.message.id
        initiator_name = "알 수 없는 사용자"

        if message_id in active_games:
            game_data = active_games[message_id]
            initiator_id = game_data['initiator_id']

            # 개설자 이름 조회
            initiator_user = self.message.guild.get_member(int(initiator_id))
            if initiator_user:
                initiator_name = initiator_user.display_name

            del active_games[message_id]

        # 모든 버튼 비활성화
        for item in self.children:
            item.disabled = True

        # 원본 메시지 수정
        await self.message.edit(
            content=f"⚠️ {initiator_name}님의 홀짝 게임이 **종료되었습니다.** (도전자 없음)",
            view=self
        )


# --- 명령어 정의 ---

# ===== 1단계: 명령어 실행자의 선택 및 게임 생성 =====
@bot.tree.command(name="홀짝도박", description="홀짝을 선택하고 다른 사용자들의 도전을 받습니다.")
@app_commands.describe(
    choice="당신의 선택 (홀 또는 짝)을 고르세요.",
    bet_amount="베팅할 포인트 금액을 입력하세요."
)
@app_commands.choices(
    choice=[
        app_commands.Choice(name="홀", value="홀"),
        app_commands.Choice(name="짝", value="짝"),
    ]
)
async def coin_betting_game(interaction: discord.Interaction, choice: str, bet_amount: int):
    initiator_id = str(interaction.user.id)

    if bet_amount <= 0:
        return await interaction.response.send_message("❌ 베팅 금액은 1점 이상이어야 합니다.", ephemeral=True)
    if get_user_points(initiator_id) < bet_amount:
        return await interaction.response.send_message(f"❌ 베팅 금액 **{bet_amount}점**이 부족합니다.", ephemeral=True)

    temp_game_id = interaction.id
    active_games[temp_game_id] = {
        'initiator_id': initiator_id,
        'initiator_choice': choice,
        'bet_amount': bet_amount,
        'challenged': []
    }

    challenge_view = ChallengeView()

    await interaction.response.send_message(
        f"🎲 **홀짝 도박 게임 시작!**\n\n"
        f"**도전자 모집:** {interaction.user.display_name}님이 **{bet_amount}점**을 걸고 홀/짝 중 하나를 선택했습니다.\n"
        f"**규칙:** 아래 버튼을 눌러 {bet_amount}점을 걸고 **{interaction.user.display_name}님의 선택**에 도전하세요! (한 번 도전 시 게임 종료)",
        view=challenge_view
    )

    message = await interaction.original_response()
    message_id = message.id

    # 🟢 타임아웃 오류 방지: message 객체를 ChallengeView 인스턴스에 할당
    challenge_view.message = message

    # 키를 상호작용 ID에서 실제 메시지 ID로 변경
    active_games[message_id] = active_games.pop(temp_game_id)

# 🌟🌟🌟 추가된 부분: 개인 포인트 초기화 🌟🌟🌟
@bot.tree.command(name="개인포인트초기화", description="특정 유저의 모든 포인트(현재/총 획득)를 0으로 초기화합니다. (관리자 전용)")
@app_commands.describe(user="포인트를 초기화할 유저")
async def reset_single_user_points(interaction: discord.Interaction, user: discord.Member):
    if not is_owner(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    uid = str(user.id)

    # 현재 포인트와 총 획득 포인트를 백업 (로그용)
    deleted_points = data["points"].get(uid, 0)
    deleted_earned = data["earned_points"].get(uid, 0)

    # 데이터 초기화
    if uid in data["points"]:
        del data["points"][uid]
    if uid in data["earned_points"]:
        del data["earned_points"][uid]

    save_data(data)

    log_command("개인포인트초기화", interaction.user.display_name,
                deleted_points,
                f"대상: {user.display_name}, 총 획득 포인트 초기화됨: {deleted_earned}점")

    await interaction.response.send_message(
        f"✅ {user.display_name}님의 **현재 포인트({deleted_points}점)**와 **총 획득 포인트({deleted_earned}점)**가 **모두 초기화**되었습니다."
    )


# 🌟🌟🌟 추가된 부분 끝 🌟🌟🌟


@bot.tree.command(name="포인트송금", description="다른 유저에게 포인트 송금 (수수료 10점 차감)")
@app_commands.describe(user="포인트를 받을 유저", amount="송금할 포인트 수")
async def transfer_points(interaction: discord.Interaction, user: discord.Member, amount: int):
    sender_uid = str(interaction.user.id)
    receiver_uid = str(user.id)

    if amount <= 0:
        return await interaction.response.send_message("❌ 송금액은 0보다 커야 합니다.", ephemeral=True)

    if sender_uid == receiver_uid:
        return await interaction.response.send_message("❌ 자신에게 포인트를 송금할 수 없습니다.", ephemeral=True)

    sender_points = get_user_points(sender_uid)

    # 총 차감액 = 송금액 + 수수료
    total_deduction = amount + TRANSFER_FEE

    if sender_points < total_deduction:
        return await interaction.response.send_message(
            f"❌ 포인트 부족! 송금액({amount}) + 수수료({TRANSFER_FEE}) = **{total_deduction}점** 필요 (현재: {sender_points}점)",
            ephemeral=True
        )

    # 1. 송금자 포인트 차감 (송금액 + 수수료)
    data["points"][sender_uid] = sender_points - total_deduction

    # 2. 수신자 포인트 지급 (송금액)
    data["points"][receiver_uid] = get_user_points(receiver_uid) + amount

    # 3. 데이터 저장
    save_data(data)

    # 4. 로그 기록
    log_point_usage(interaction.user.display_name, total_deduction, f"송금({amount}점) + 수수료({TRANSFER_FEE})")
    log_command("포인트송금", interaction.user.display_name, amount, f"대상: {user.display_name}, 수수료: {TRANSFER_FEE}")

    await interaction.response.send_message(
        f"✅ {user.display_name}에게 **{amount}**포인트 송금 완료! (수수료 **{TRANSFER_FEE}점** 차감) \n"
        f"➡️ **남은 포인트**: **{data['points'][sender_uid]}**점"
    )


# 개개인의 차감 전 총 획득 포인트 조회 기능 (관리자 전용)
@bot.tree.command(name="총획득포인트조회", description="차감되지 않은 총 획득 포인트를 조회합니다. (관리자 전용)")
@app_commands.describe(user="조회할 유저 (선택 사항, 미입력 시 본인)")
async def total_earned_points_check(interaction: discord.Interaction, user: discord.Member = None):
    if not is_whitelist(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    target_user = user if user else interaction.user
    uid = str(target_user.id)

    # 총 획득 포인트 조회
    total_earned = get_user_total_earned(uid)

    # 현재 포인트 조회 (참고용)
    current_points = get_user_points(uid)

    await interaction.response.send_message(
        f"📈 **{target_user.display_name}**님의 포인트 현황:\n"
        f"• **총 획득 포인트 (차감 전)**: **{total_earned}점**\n"
        f"• **현재 보유 포인트**: **{current_points}점**"
    )


# 🌟 출석 체크 명령어
@bot.tree.command(name="출석", description="매일 출석 체크하고 포인트 획득!")
async def attendance(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # 출석 데이터 초기화 또는 가져오기
    data.setdefault("attendance", {}).setdefault(uid, {'last_date': None, 'streak': 0})
    user_att = data["attendance"][uid]
    last_check_date_str = user_att['last_date']
    current_streak = user_att['streak']

    if last_check_date_str == today:
        return await interaction.response.send_message("❌ 이미 오늘 출석 체크를 완료했습니다. 내일 다시 시도해주세요.", ephemeral=True)

    # --- 연속 출석 및 포인트 계산 로직 ---
    reward = ATTENDANCE_REWARD
    bonus_msg = ""

    # 어제 날짜 확인
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. 연속 출석 여부 확인 및 갱신
    if last_check_date_str == yesterday:
        # 연속 출석 성공
        new_streak = current_streak + 1
    elif last_check_date_str is None or last_check_date_str != today:
        # 첫 출석 또는 연속 출석 실패 후 재시작
        new_streak = 1

    # 2. 보너스 지급 확인 (7회마다)
    if new_streak > 0 and new_streak % DAILY_BONUS_COUNT == 0:
        reward += DAILY_BONUS_REWARD
        bonus_msg = f"🎉 **{DAILY_BONUS_COUNT}회 연속 출석 보너스** {DAILY_BONUS_REWARD}점 추가 획득! (총 {ATTENDANCE_REWARD + DAILY_BONUS_REWARD}점)"

    # 3. 포인트 지급
    data["points"][uid] = get_user_points(uid) + reward
    data.setdefault("earned_points", {})
    data["earned_points"][uid] = data["earned_points"].get(uid, 0) + reward

    # 4. 출석 정보 업데이트
    data["attendance"][uid]['last_date'] = today
    data["attendance"][uid]['streak'] = new_streak
    save_data(data)

    log_command("출석체크", interaction.user.display_name, reward)

    response_msg = (
        f"✅ **출석 체크 완료!** **{ATTENDANCE_REWARD}**포인트 획득.\n"
        f"{bonus_msg}\n"
        f"➡️ **총 획득 포인트**: **{reward}점** (현재 포인트: {data['points'][uid]}점)\n"
        f"🔥 **현재 연속 출석**: **{new_streak}일**"
    )

    await interaction.response.send_message(response_msg)


# 🌟 수동 레벨업 명령어
@bot.tree.command(name="레벨업", description=f"포인트로 레벨을 올립니다. (비용: {LEVEL_UP_COST} 포인트)")
async def level_up(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    points = get_user_points(uid)
    current_level = get_user_level(uid)

    if points < LEVEL_UP_COST:
        return await interaction.response.send_message(
            f"❌ 레벨업에 필요한 포인트가 부족합니다. (필요: {LEVEL_UP_COST}점, 현재: {points}점)", ephemeral=True
        )

    # 포인트 차감 및 레벨 증가
    data["points"][uid] = points - LEVEL_UP_COST
    data["level"][uid] = current_level + 1
    save_data(data)

    log_point_usage(interaction.user.display_name, LEVEL_UP_COST, f"레벨업: Lv.{current_level} -> Lv.{current_level + 1}")

    await interaction.response.send_message(
        f"⬆️ **Lv.{current_level}**에서 **Lv.{current_level + 1}**로 레벨업 성공!\n"
        f"💸 **{LEVEL_UP_COST}** 포인트가 차감되었습니다. (남은 포인트: {data['points'][uid]}점)"
    )
# --- 🌟 관리자 전용 /레벨업 명령어 ---
@bot.tree.command(name="관리자레벨업", description="특정 유저의 레벨을 강제로 올립니다. (봇 운영자 전용)")
@app_commands.describe(user="레벨을 올릴 유저", amount="올릴 레벨 수")
async def level_up_admin(interaction: discord.Interaction, user: discord.Member, amount: int = 1):
    # 봇 운영자 ID 확인
    if not is_admin(str(interaction.user.id)):
        return await interaction.response.send_message(
            "❌ 이 명령어는 **봇 운영자**만 사용할 수 있습니다. (ADMIN_IDS 확인 필요)", ephemeral=True
        )

    # 레벨 수 유효성 검사
    if amount <= 0:
        return await interaction.response.send_message("올릴 레벨 수는 1 이상이어야 합니다.", ephemeral=True)

    uid = str(user.id)
    current_level = get_user_level(uid)
    new_level = current_level + amount

    # 레벨 데이터 초기화 확인 및 업데이트
    if "level" not in data:
        data["level"] = {}

    data["level"][uid] = new_level
    save_data(data)

    await interaction.response.send_message(
        f"**[관리자 전용]** {user.display_name}님의 레벨을 **{amount}**만큼 올렸습니다.\n"
        f"➡️ **Lv.{current_level}**에서 **Lv.{new_level}**로 변경되었습니다."
    )

# ===== 2. 상점 관련 =====
@bot.tree.command(name="상점변경", description="상점 아이템의 가격을 변경합니다. (관리자 전용)")
@app_commands.describe(
    item_name="가격을 변경할 아이템명",
    new_price="새로운 가격"
)
@app_commands.autocomplete(item_name=shop_item_autocomplete)
async def change_item_price(interaction: discord.Interaction, item_name: str, new_price: int):
    # 1. 관리자 권한 확인
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    # 2. 가격 유효성 검사
    if new_price <= 0:
        return await interaction.response.send_message("❌ 새로운 가격은 0보다 커야 합니다.", ephemeral=True)

    # 3. 아이템 존재 여부 확인
    if item_name not in data["shop"]:
        return await interaction.response.send_message(f"❌ 상점에 **`{item_name}`** 아이템이 없습니다. `/상점등록`을 사용하세요.",
                                                       ephemeral=True)

    # 4. 기존 가격 저장 및 가격 업데이트
    old_price = data["shop"][item_name]
    data["shop"][item_name] = new_price
    save_data(data)

    # 5. 로그 및 응답
    log_command(
        "상점변경",
        interaction.user.display_name,
        new_price,  # 로그 기록 시 새 가격을 기록
        f"{item_name} 가격 변경 ({old_price} -> {new_price})"
    )

    await interaction.response.send_message(
        f"🛒 아이템 **`{item_name}`** 가격 변경 완료!\n"
        f"➡️ **기존 가격:** {old_price}포인트\n"
        f"➡️ **새로운 가격:** **{new_price}**포인트"
    )

@bot.tree.command(name="상점등록", description="상점 아이템 등록 (관리자 전용)")
@app_commands.describe(item_name="아이템명", price="가격")
async def add_item(interaction: discord.Interaction, item_name: str, price: int):
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)
    if price <= 0:
        return await interaction.response.send_message("❌ 가격은 0보다 커야 합니다.", ephemeral=True)

    is_update = item_name in data["shop"]
    data["shop"][item_name] = price
    save_data(data)

    action = "업데이트" if is_update else "등록"
    log_command(f"상점{action}", interaction.user.display_name, price, item_name)
    await interaction.response.send_message(f"🛒 아이템 **`{item_name}`** {action} 완료 (가격: {price}포인트)")


@bot.tree.command(name="상점삭제", description="상점 아이템 삭제 (관리자 전용)")
@app_commands.describe(item_name="삭제할 아이템")
@app_commands.autocomplete(item_name=shop_item_autocomplete)
async def remove_shop_item(interaction: discord.Interaction, item_name: str):
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)
    if item_name not in data["shop"]:
        return await interaction.response.send_message("❌ 상점에 없는 아이템입니다.", ephemeral=True)

    deleted_price = data["shop"][item_name]
    del data["shop"][item_name]
    save_data(data)
    log_command("상점삭제", interaction.user.display_name, deleted_price, item_name)
    await interaction.response.send_message(f"🗑 아이템 **`{item_name}`** 삭제 완료")


@bot.tree.command(name="상점", description="상점 목록 확인")
async def shop_list(interaction: discord.Interaction):
    if not data["shop"]:
        return await interaction.response.send_message("🛍 상점이 비어 있습니다. 관리자에게 문의하세요.")

    embed = discord.Embed(title="🛒 서버 상점 목록", color=discord.Color.blue())
    items_list = []
    for item, price in data["shop"].items():
        items_list.append(f"• **{item}**: {price}점")

    embed.description = "\n".join(items_list)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="구매", description="상점 아이템 구매")
@app_commands.describe(item_name="구매할 아이템")
@app_commands.autocomplete(item_name=shop_item_autocomplete)
async def buy_item(interaction: discord.Interaction, item_name: str):
    uid = str(interaction.user.id)
    points = get_user_points(uid)

    if item_name not in data["shop"]:
        return await interaction.response.send_message("❌ 상점에 없는 아이템입니다.", ephemeral=True)

    price = data["shop"][item_name]
    if points < price:
        return await interaction.response.send_message(
            f"❌ 포인트 부족! (현재: {points}점, 필요: {price}점)", ephemeral=True
        )

    # 포인트 차감 및 인벤토리 추가
    data["points"][uid] = points - price
    data.setdefault("inventory", {}).setdefault(uid, {}).setdefault(item_name, 0)
    data["inventory"][uid][item_name] += 1
    save_data(data)

    log_point_usage(interaction.user.display_name, price, f"구매: {item_name}")  # '포인트사용' 로그
    log_command("구매", interaction.user.display_name, price, item_name)  # '구매' 로그

    await interaction.response.send_message(
        f"✅ **{item_name}** 구매 완료! (남은 포인트: **{data['points'][uid]}**점)"
    )


@bot.tree.command(name="인벤토리", description="내가 가진 아이템 목록 확인")
async def check_inventory(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    inv = data.get("inventory", {}).get(uid, {})

    if not inv:
        return await interaction.response.send_message("📦 인벤토리가 비어 있습니다.")

    embed = discord.Embed(title=f"📦 {interaction.user.display_name}님의 인벤토리", color=discord.Color.dark_green())
    items_list = []
    for item, count in inv.items():
        items_list.append(f"• **{item}**: {count}개")

    embed.description = "\n".join(items_list)
    await interaction.response.send_message(embed=embed)


# ===== 9. 인벤토리 관리 (업데이트) =====
@bot.tree.command(name="인벤토리삭제아이템", description="관리자가 유저 인벤토리 특정 아이템 삭제 (관리자 전용)")
@app_commands.describe(user="삭제할 유저", item_name="삭제할 아이템 이름")
@app_commands.autocomplete(item_name=shop_item_autocomplete)
async def delete_inventory_item(interaction: discord.Interaction, user: discord.Member, item_name: str):
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    uid = str(user.id)
    user_inv = data.get("inventory", {}).get(uid, {})

    if not user_inv or item_name not in user_inv:
        return await interaction.response.send_message(f"❌ {user.display_name}님의 인벤토리에 **`{item_name}`**이(가) 없습니다.",
                                                       ephemeral=True)

    # 아이템 카운트를 1 감소시키거나, 0이 되면 항목을 삭제
    data["inventory"][uid][item_name] -= 1
    if data["inventory"][uid][item_name] <= 0:
        del data["inventory"][uid][item_name]

    # 만약 유저 인벤토리가 비면 유저 항목 삭제
    if not data["inventory"][uid]:
        del data["inventory"][uid]

    save_data(data)
    log_command("인벤토리아이템삭제", interaction.user.display_name, extra=f"대상: {user.display_name}, 아이템: {item_name}")
    await interaction.response.send_message(f"✅ {user.display_name}님의 **`{item_name}`** 1개 삭제 완료")


# ===== 10. 로그 조회 기능 =====
@bot.tree.command(name="로그조회", description="전체 로그 확인 (관리자 전용)")
@app_commands.describe(user="특정 유저 로그만 보기 (선택 사항)")
async def view_logs(interaction: discord.Interaction, user: discord.Member = None):
    if not is_whitelist(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        return await interaction.response.send_message("📄 로그가 존재하지 않습니다.")

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    # 유저별 필터링
    if user:
        uid_name = user.display_name
        logs = [log for log in logs if log.get("user") == uid_name]

    if not logs:
        return await interaction.response.send_message("📄 해당 조건의 로그가 없습니다.")

    # 최근 로그 20개만 표시
    logs_to_display = logs[-20:]

    msg = ""
    for log in logs_to_display:
        time = log.get("time", "N/A").split(" ")[1]  # 시간만 표시
        cmd = log.get("command", "")
        usr = log.get("user", "")
        amt = log.get("amount", "")
        extra = log.get("extra", "")

        log_line = f"[{time}] **{usr}** / {cmd}"
        if amt is not None:
            log_line += f" / {amt}점"
        if extra:
            log_line += f" / {extra}"

        msg += log_line + "\n"

    embed = discord.Embed(title="📄 봇 활동 로그 (최근 20개)", color=discord.Color.light_grey())
    embed.description = msg

    await interaction.response.send_message(embed=embed)


# ===== 3. 포인트 도박 =====
@bot.tree.command(name="포인트도박", description="포인트 홀짝 도박")
@app_commands.describe(amount="걸 포인트", choice="홀/짝 선택")
@app_commands.choices(choice=[app_commands.Choice(name="홀", value="홀"),
                              app_commands.Choice(name="짝", value="짝")])
async def gamble(interaction: discord.Interaction, amount: int, choice: app_commands.Choice[str]):
    uid = str(interaction.user.id)
    points = get_user_points(uid)

    if amount <= 0:
        return await interaction.response.send_message("❌ 베팅 금액은 0보다 커야 합니다.", ephemeral=True)
    if points < amount:
        return await interaction.response.send_message(f"❌ 포인트 부족! (현재: {points}점)", ephemeral=True)

    roll = random.randint(1, 100)
    result = "짝" if roll % 2 == 0 else "홀"

    if choice.value == result:
        # 베팅 금액의 100% 획득
        win = int(amount * 1)
        data["points"][uid] += win
        msg = f"🎉 **성공!** 숫자: `{roll}` ({result}!) - **{win}**포인트 획득!"
        log_command("도박(승)", interaction.user.display_name, win, f"{choice.value}에 {amount} 베팅")
        data.setdefault("earned_points", {}).setdefault(uid, 0)
        data["earned_points"][uid] += win
    else:
        # 베팅 금액 전체 손실
        data["points"][uid] -= amount
        msg = f"😂 **실패!** 숫자: `{roll}` ({result}...) - **{amount}**포인트 손실!"
        log_command("도박(패)", interaction.user.display_name, -amount, f"{choice.value}에 {amount} 베팅")
        log_point_usage(interaction.user.display_name, -amount, f"도박 패배({choice.value})")  # 마이너스로 기록

    save_data(data)

    await interaction.response.send_message(msg + f"\n➡️ **현재 포인트**: **{data['points'][uid]}**점")


# ===== 4. 역할 관리 =====
@bot.tree.command(name="역할추가", description="유저 역할 추가 (관리자 전용)")
@app_commands.describe(user="역할을 추가할 유저", role_id="추가할 역할")
@app_commands.autocomplete(role_id=role_autocomplete)
async def add_role(interaction: discord.Interaction, user: discord.Member, role_id: str):
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    role = interaction.guild.get_role(int(role_id))
    if not role:
        return await interaction.response.send_message("❌ 해당 ID의 역할을 찾을 수 없습니다.", ephemeral=True)

    if role in user.roles:
        return await interaction.response.send_message(f"❌ {user.display_name}님은 이미 **`{role.name}`** 역할을 가지고 있습니다.",
                                                       ephemeral=True)

    try:
        await user.add_roles(role)
        log_command("역할추가", interaction.user.display_name, extra=f"대상: {user.display_name}, 역할: {role.name}")
        await interaction.response.send_message(f"✅ {user.display_name}에게 **`{role.name}`** 역할 추가 완료")
    except discord.Forbidden:
        await interaction.response.send_message("❌ 봇의 권한이 부족하여 역할을 추가할 수 없습니다.", ephemeral=True)
    except Exception as e:
        print(f"역할 추가 중 오류: {e}")
        await interaction.response.send_message("❌ 역할 추가 중 알 수 없는 오류 발생", ephemeral=True)


@bot.tree.command(name="역할제거", description="유저 역할 제거 (관리자 전용)")
@app_commands.describe(user="역할을 제거할 유저", role_id="제거할 역할")
@app_commands.autocomplete(role_id=role_autocomplete)
async def remove_role(interaction: discord.Interaction, user: discord.Member, role_id: str):
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    role = interaction.guild.get_role(int(role_id))
    if not role:
        return await interaction.response.send_message("❌ 해당 ID의 역할을 찾을 수 없습니다.", ephemeral=True)

    if role not in user.roles:
        return await interaction.response.send_message(f"❌ {user.display_name}님은 **`{role.name}`** 역할을 가지고 있지 않습니다.",
                                                       ephemeral=True)

    try:
        await user.remove_roles(role)
        log_command("역할제거", interaction.user.display_name, extra=f"대상: {user.display_name}, 역할: {role.name}")
        await interaction.response.send_message(f"✅ {user.display_name}에게서 **`{role.name}`** 역할 제거 완료")
    except discord.Forbidden:
        await interaction.response.send_message("❌ 봇의 권한이 부족하여 역할을 제거할 수 없습니다.", ephemeral=True)
    except Exception as e:
        print(f"역할 제거 중 오류: {e}")
        await interaction.response.send_message("❌ 역할 제거 중 알 수 없는 오류 발생", ephemeral=True)


# ===== 5. 백업 / 초기화 =====
@bot.tree.command(name="백업", description="데이터 백업 (관리자 전용)")
async def backup_data(interaction: discord.Interaction):
    if not is_owner(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    backup_file = f"data_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        await interaction.response.send_message(f"✅ 데이터 백업 완료: **`{backup_file}`**")
    except Exception as e:
        print(f"백업 중 오류 발생: {e}")
        await interaction.response.send_message("❌ 백업 중 오류가 발생했습니다.", ephemeral=True)


@bot.tree.command(name="초기화", description="전체 데이터 초기화 (관리자 전용)")
async def reset_all(interaction: discord.Interaction):
    if not is_owner(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    # 초기화 확인 버튼 추가 (옵션)
    await interaction.response.send_message(
        "⚠️ **경고!** 모든 포인트, 상점, 인벤토리 데이터가 **영구적으로 삭제**됩니다. 정말로 초기화하시겠습니까? (/최종초기화 를 실행해야 완료됩니다.)",
        ephemeral=True
    )


@bot.tree.command(name="최종초기화", description="정말로 모든 데이터를 초기화합니다. (관리자 전용 최종 확인)")
async def final_reset_all(interaction: discord.Interaction):
    if not is_owner(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    global data
    # level을 수동 레벨로 변경했으므로, 초기화 시점에는 level: {}로 두는 것이 적절합니다.
    data = {"points": {}, "earned_points": {}, "shop": {}, "inventory": {}, "attendance": {}, "level": {}}
    save_data(data)
    log_command("전체초기화", interaction.user.display_name, extra="모든 봇 데이터 초기화됨")
    await interaction.response.send_message("✅ **모든 데이터**가 성공적으로 **초기화**되었습니다.")


# ===== 6. 공지 =====
@bot.tree.command(name="공지", description="공지 전송 (관리자 전용)")
@app_commands.describe(channel="공지를 보낼 채널", message="공지 내용")
async def send_announcement(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 관리자 권한 필요", ephemeral=True)

    try:
        embed = discord.Embed(title="📢 서버 공지사항", description=message, color=discord.Color.red())
        embed.set_footer(text=f"공지 작성자: {interaction.user.display_name}")
        embed.timestamp = datetime.datetime.now()

        await channel.send(embed=embed)

        log_command("공지", interaction.user.display_name, extra=f"채널: {channel.name}, 내용 길이: {len(message)}")
        await interaction.response.send_message(f"✅ **`{channel.name}`** 채널에 공지 전송 완료", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message(f"❌ 봇의 권한이 부족하여 **`{channel.name}`** 채널에 메시지를 보낼 수 없습니다.",
                                                ephemeral=True)
    except Exception as e:
        print(f"공지 전송 중 오류: {e}")
        await interaction.response.send_message("❌ 공지 전송 중 알 수 없는 오류 발생", ephemeral=True)


# ===== 7. 순위 / 레벨링 =====

@bot.tree.command(name="서버총포인트", description="서버 내 모든 유저의 현재 포인트 합계 확인")
async def total_server_points(interaction: discord.Interaction):
    total_points = sum(data.get("points", {}).values())

    await interaction.response.send_message(
        f"💰 **서버 전체 현재 포인트 합계**: **{total_points}점**"
    )


@bot.tree.command(name="내순위", description="포인트 기준 내 순위 확인")
async def my_rank(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    guild = interaction.guild

    filtered_points = {k: v for k, v in data.get("points", {}).items() if v > 0}

    if not filtered_points:
        return await interaction.response.send_message(" 서버에 포인트 기록이 있는 유저가 없습니다.", ephemeral=True)

    sorted_points = sorted(filtered_points.items(), key=lambda x: x[1], reverse=True)

    found = False
    for i, (user_id, pts) in enumerate(sorted_points, start=1):
        if user_id == uid:
            found = True

            # 내 레벨
            my_level = get_user_level(uid)

            # 상위 3명 리스트를 먼저 만듦
            top_ranks = []
            for j in range(min(3, len(sorted_points))):
                top_uid, top_pts = sorted_points[j]

                # 멤버 객체를 가져오려고 시도 (서버에 있는 경우)
                top_member = guild.get_member(int(top_uid))
                top_level = get_user_level(top_uid)

                if top_member:
                    # 서버에 있다면 현재 닉네임 사용
                    top_name = top_member.display_name
                else:
                    # 서버에 없거나 정보를 가져올 수 없다면 ID를 표시
                    top_name = f"미접속/탈퇴 유저 ({top_uid[:4]}...)"

                top_ranks.append(f"#{j + 1} **{top_name}** (Lv.{top_level}): {top_pts}점")

            embed = discord.Embed(title="🏆 포인트 순위 정보", color=discord.Color.gold())
            embed.add_field(name="✨ 내 순위",
                            value=f"**{interaction.user.display_name}**님은 **Lv.{my_level}**, **{i}위**이며, **{pts}점**을 보유 중입니다.",
                            inline=False)
            embed.add_field(name="🥇 서버 TOP 3", value="\n".join(top_ranks), inline=False)

            await interaction.response.send_message(embed=embed)
            return

    if not found:
        await interaction.response.send_message("❌ 포인트 기록이 없어 순위를 확인할 수 없습니다.", ephemeral=True)

'''
@bot.tree.command(name="수뇌부명단", description="수뇌부 명단을 보여줍니다.")
async def 수뇌부명단(interaction: discord.Interaction):
    guild = interaction.guild
    members = []

    for admin_id in ADMIN_IDS:
        member = guild.get_member(int(admin_id))
        if member:
            members.append(member.mention)

    if not members:
        await interaction.response.send_message("⚠️ 수뇌부를 찾을 수 없습니다.")
        return

    embed = discord.Embed(title="🏛 수뇌부 명단", description="\n".join(members), color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

# === 인사 보고서 ===
@bot.tree.command(name="인사보고서", description="인사 혹은 상/벌점 보고서를 전송합니다.")
@app_commands.describe(
    report_type="보고서 종류 선택 (상벌점 또는 인사)",
    target="대상자 이름 또는 멘션",
    reason="사유 입력",
    value="상벌점 수 또는 직급"
)
async def 인사보고서(interaction: discord.Interaction, report_type: str, target: str, reason: str, value: str):
    # 관리자 체크
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return

    # 채널 ID 기반 검색
    channel = interaction.guild.get_channel(1437694396479832086)
    if not channel:
        await interaction.response.send_message("❌ 인사보고서 채널을 찾을 수 없습니다.", ephemeral=True)
        return

    # 보고서 생성
    if report_type == "상벌점":
        embed = discord.Embed(title="📋 상/벌점 보고서", color=discord.Color.blue())
        embed.add_field(name="집행자", value=interaction.user.mention, inline=False)
        embed.add_field(name="대상자", value=target, inline=False)
        embed.add_field(name="사유", value=reason, inline=False)
        embed.add_field(name="상/벌점 수", value=value, inline=False)
    else:
        embed = discord.Embed(title="📝 인사 보고서", color=discord.Color.green())
        embed.add_field(name="작성자", value=interaction.user.mention, inline=False)
        embed.add_field(name="대상자", value=target, inline=False)
        embed.add_field(name="사유", value=reason, inline=False)
        embed.add_field(name="헌병대 직급", value=value, inline=False)

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ 보고서가 정상적으로 전송되었습니다.", ephemeral=True)

# 관리자 멘션용 역할 ID (예시, 실제 ID로 변경)
MPC_ROLE_ID = 123456789012345678  # 헌병대장
MPUC_ROLE_ID = 987654321098765432  # 헌병부대장

MENTION_STR = f"<@&{MPC_ROLE_ID}> | MPC <@&{MPUC_ROLE_ID}> | MPUC"

# 근무 보고서
@bot.tree.command(name="근무보고서", description="근무 보고서를 전송합니다.")
@app_commands.describe(
    colleagues="근무 동료 (쉼표로 구분)",
    work_time="근무 시간",
    work_place="근무 장소",
    work_photo="근무 사진 첨부",
    count_photo="카운트 사진 첨부"
)
async def 근무보고서(
    interaction: discord.Interaction,
    colleagues: str,
    work_time: str,
    work_place: str,
    work_photo: discord.Attachment = None,
    count_photo: discord.Attachment = None
):
    channel = interaction.guild.get_channel(1437694396479832086)
    if not channel:
        await interaction.response.send_message("❌ 활동 보고서 채널을 찾을 수 없습니다.", ephemeral=True)
        return

    embed = discord.Embed(title="근무 보고서", color=discord.Color.green())
    embed.add_field(name="작성자", value=interaction.user.mention, inline=False)
    embed.add_field(name="동료", value=colleagues, inline=False)
    embed.add_field(name="근무 시간", value=work_time, inline=False)
    embed.add_field(name="근무 장소", value=work_place, inline=False)

    if work_photo:
        embed.set_image(url=work_photo.url)
    if count_photo:
        embed.set_thumbnail(url=count_photo.url)

    await channel.send(content=MENTION_STR, embed=embed)
    await interaction.response.send_message("✅ 근무 보고서가 전송되었습니다.", ephemeral=True)


# 전출 보고서
@bot.tree.command(name="전출보고서", description="전출 보고서를 전송합니다.")
@app_commands.describe(
    target="전출 대상자",
    reason="전출 사유"
)
async def 전출보고서(interaction: discord.Interaction, target: str, reason: str):
    channel = interaction.guild.get_channel(1437694396479832086)
    if not channel:
        await interaction.response.send_message("❌ 활동 보고서 채널을 찾을 수 없습니다.", ephemeral=True)
        return

    embed = discord.Embed(title="전출 보고서", color=discord.Color.orange())
    embed.add_field(name="작성자", value=interaction.user.mention, inline=False)
    embed.add_field(name="대상자", value=target, inline=False)
    embed.add_field(name="사유", value=reason, inline=False)

    await channel.send(content=MENTION_STR, embed=embed)
    await interaction.response.send_message("✅ 전출 보고서가 전송되었습니다.", ephemeral=True)


# 전역 보고서
@bot.tree.command(name="전역보고서", description="전역 보고서를 전송합니다.")
@app_commands.describe(
    target="전역 대상자",
    reason="전역 사유"
)
async def 전역보고서(interaction: discord.Interaction, target: str, reason: str):
    channel = interaction.guild.get_channel(1437694396479832086)
    if not channel:
        await interaction.response.send_message("❌ 활동 보고서 채널을 찾을 수 없습니다.", ephemeral=True)
        return

    embed = discord.Embed(title="전역 보고서", color=discord.Color.purple())
    embed.add_field(name="작성자", value=interaction.user.mention, inline=False)
    embed.add_field(name="대상자", value=target, inline=False)
    embed.add_field(name="사유", value=reason, inline=False)

    await channel.send(content=MENTION_STR, embed=embed)
    await interaction.response.send_message("✅ 전역 보고서가 전송되었습니다.", ephemeral=True)


# 집합/훈련 참여 보고서
@bot.tree.command(name="집합훈련보고서", description="집합/훈련 참여 보고서를 전송합니다.")
@app_commands.describe(
    organizer="개최자 이름",
    event_type="집합/훈련 종류",
    count="보고서 횟수"
)
async def 집합훈련보고서(interaction: discord.Interaction, organizer: str, event_type: str, count: str):
    channel = interaction.guild.get_channel(1437694396479832086)
    if not channel:
        await interaction.response.send_message("❌ 활동 보고서 채널을 찾을 수 없습니다.", ephemeral=True)
        return

    embed = discord.Embed(title="집합/훈련 참여 보고서", color=discord.Color.blue())
    embed.add_field(name="작성자", value=interaction.user.mention, inline=False)
    embed.add_field(name="개최자", value=organizer, inline=False)
    embed.add_field(name="집합/훈련 종류", value=event_type, inline=False)
    embed.add_field(name="보고서 횟수", value=count, inline=False)

    await channel.send(content=MENTION_STR, embed=embed)
    await interaction.response.send_message("✅ 집합/훈련 보고서가 전송되었습니다.", ephemeral=True)

# ===== 8. 환영 / 작별 메시지 =====
@bot.event
async def on_member_join(member):
    # 'general' 채널을 찾습니다. 서버마다 이름이 다를 수 있으므로 ID를 사용하거나 환경에 맞게 조정하는 것이 좋습니다.
    # 여기서는 'general'이라는 이름을 가진 텍스트 채널을 찾아봅니다.
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        try:
            await channel.send(f"👋 **{member.mention}**님, 서버에 오신 것을 환영합니다! 🎉")
        except discord.Forbidden:
            print(f"❌ '{channel.name}' 채널에 메시지 전송 권한이 없습니다.")
'''

# 🌟 포인트 순위표 명령어
@bot.tree.command(name="순위표", description="서버 포인트 전체 순위표를 확인합니다 (최대 10위)")
async def leaderboard(interaction: discord.Interaction):
    guild = interaction.guild

    # 포인트가 0 초과인 유저만 필터링
    filtered_points = {k: v for k, v in data.get("points", {}).items() if v > 0}

    if not filtered_points:
        return await interaction.response.send_message("📊 포인트 기록이 있는 유저가 없어 순위를 표시할 수 없습니다.")

    # 포인트 기준 내림차순 정렬
    sorted_points = sorted(filtered_points.items(), key=lambda item: item[1], reverse=True)

    embed = discord.Embed(title="📊 서버 포인트 순위표 (Lv & Point)", color=discord.Color.teal())
    embed.set_footer(text=f"기준: 현재 보유 포인트 | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

    rank_list = []

    # 상위 10명만 표시
    for i, (uid, points) in enumerate(sorted_points[:10]):
        member = guild.get_member(int(uid))
        level = get_user_level(uid)

        # 닉네임 형식 지정
        if member:
            name = member.display_name
        else:
            name = f"미접속/탈퇴 유저 ({uid[:4]}...)"

        rank = i + 1

        # 1, 2, 3위는 이모지와 굵게 표시로 강조
        if rank == 1:
            emoji = "🥇"
            name_format = f"**{name}**"
        elif rank == 2:
            emoji = "🥈"
            name_format = f"**{name}**"
        elif rank == 3:
            emoji = "🥉"
            name_format = f"**{name}**"
        else:
            emoji = "✨"
            name_format = name

        rank_list.append(f"{emoji} **#{rank}** {name_format} (Lv.{level}): **{points}점**")

    embed.description = "\n".join(rank_list)

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_member_remove(member):
    # 'general' 채널을 찾습니다.
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        try:
            await channel.send(f"👋 **{member.display_name}**님이 서버를 떠났습니다.")
        except discord.Forbidden:
            print(f"❌ '{channel.name}' 채널에 메시지 전송 권한이 없습니다.")


# ===== 봇 실행 =====
if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN":
        print("❌ 오류: 봇 토큰을 'YOUR_BOT_TOKEN' 대신 실제 토큰으로 교체해야 합니다.")
    else:
        try:
            print("⏳ 봇 연결을 시도 중...")
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ 오류: 토큰이 유효하지 않거나 로그인에 실패했습니다. 토큰을 확인해주세요.")
        except Exception as e:

            print(f"❌ 봇 실행 중 치명적인 오류 발생: {type(e).__name__}: {e}")



